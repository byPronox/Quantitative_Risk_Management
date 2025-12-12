"""
PostgreSQL Repository for NVD service (replaces MongoDB)
Uses Supabase as the PostgreSQL provider
"""
import logging
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import time
import asyncio
from contextlib import asynccontextmanager

import httpx
from ..config.settings import settings

logger = logging.getLogger(__name__)


class PostgresRepository:
    """Repository for PostgreSQL/Supabase operations in NVD microservice"""
    
    def __init__(self):
        self.database_url = settings.DATABASE_URL
        self.connection = None
        self._pool = None
        self.time_api_url = "http://worldtimeapi.org/api/timezone/Etc/UTC"
    
    async def _get_current_time(self) -> datetime:
        """
        Get current time from WorldTimeAPI with fallback to system time.
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(self.time_api_url)
                if response.status_code == 200:
                    data = response.json()
                    external_time = datetime.fromisoformat(data["datetime"])
                    logger.debug(f"Using WorldTimeAPI time: {external_time}")
                    return external_time
        except Exception as e:
            logger.warning(f"WorldTimeAPI failed, using system time: {e}")
        
        return datetime.utcnow()
    
    async def connect(self):
        """Connect to PostgreSQL/Supabase"""
        try:
            import asyncpg
            
            self._pool = await asyncpg.create_pool(
                self.database_url,
                min_size=2,
                max_size=10,
                command_timeout=60
            )
            
            # Create tables if not exist
            await self._create_tables()
            logger.info("PostgreSQL connection established")
            
        except Exception as e:
            logger.error("Failed to connect to PostgreSQL: %s", str(e))
            raise
    
    async def disconnect(self):
        """Disconnect from PostgreSQL"""
        if self._pool:
            await self._pool.close()
            logger.info("PostgreSQL connection closed")
    
    async def _create_tables(self):
        """Create necessary tables for NVD data"""
        async with self._pool.acquire() as conn:
            # Create nvd_jobs table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS nvd_jobs (
                    id SERIAL PRIMARY KEY,
                    job_id VARCHAR(255) UNIQUE NOT NULL,
                    keyword VARCHAR(255) NOT NULL,
                    status VARCHAR(50) DEFAULT 'pending',
                    total_results INTEGER DEFAULT 0,
                    processed_at TIMESTAMP WITH TIME ZONE,
                    processed_via VARCHAR(100) DEFAULT 'nvd_microservice',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """)
            
            # Create nvd_vulnerabilities table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS nvd_vulnerabilities (
                    id SERIAL PRIMARY KEY,
                    job_id VARCHAR(255) REFERENCES nvd_jobs(job_id) ON DELETE CASCADE,
                    cve_id VARCHAR(50) NOT NULL,
                    source_identifier VARCHAR(255),
                    published TIMESTAMP WITH TIME ZONE,
                    last_modified TIMESTAMP WITH TIME ZONE,
                    vuln_status VARCHAR(100),
                    description TEXT,
                    cvss_v3_score DECIMAL(3,1),
                    cvss_v3_severity VARCHAR(20),
                    cvss_v2_score DECIMAL(3,1),
                    raw_data JSONB,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    UNIQUE(job_id, cve_id)
                )
            """)
            
            # Create indexes
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_nvd_jobs_keyword ON nvd_jobs(keyword)
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_nvd_jobs_processed_at ON nvd_jobs(processed_at DESC)
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_nvd_vulns_cve_id ON nvd_vulnerabilities(cve_id)
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_nvd_vulns_severity ON nvd_vulnerabilities(cvss_v3_severity)
            """)
            
            logger.info("NVD tables created/verified successfully")
    
    async def save_jobs(self, jobs_data: List[Dict[str, Any]]):
        """Save job results to PostgreSQL"""
        if not self._pool:
            await self.connect()
        
        current_time = await self._get_current_time()
        
        async with self._pool.acquire() as conn:
            for job in jobs_data:
                if job.get("status") == "completed" and job.get("vulnerabilities"):
                    job_id = job.get("job_id", "")
                    keyword = job.get("keyword", "")
                    status = job.get("status", "pending")
                    total_results = int(job.get("total_results", 0))
                    processed_at = job.get("timestamp", current_time.timestamp())
                    processed_via = job.get("processed_via", "nvd_microservice")
                    
                    # Convert timestamp to datetime if needed
                    if isinstance(processed_at, (int, float)):
                        processed_at = datetime.fromtimestamp(processed_at)
                    
                    # Insert or update job
                    await conn.execute("""
                        INSERT INTO nvd_jobs (job_id, keyword, status, total_results, processed_at, processed_via, updated_at)
                        VALUES ($1, $2, $3, $4, $5, $6, $7)
                        ON CONFLICT (job_id) DO UPDATE SET
                            status = EXCLUDED.status,
                            total_results = EXCLUDED.total_results,
                            processed_at = EXCLUDED.processed_at,
                            updated_at = EXCLUDED.updated_at
                    """, job_id, keyword, status, total_results, processed_at, processed_via, current_time)
                    
                    # Insert vulnerabilities
                    for vuln in job.get("vulnerabilities", []):
                        if "cve" in vuln:
                            cve_data = vuln["cve"]
                            cve_id = cve_data.get("id", "")
                            source_id = cve_data.get("sourceIdentifier", "")
                            
                            # Parse dates
                            published = self._parse_datetime(cve_data.get("published"))
                            last_modified = self._parse_datetime(cve_data.get("lastModified"))
                            
                            vuln_status = cve_data.get("vulnStatus", "Unknown")
                            
                            # Get description (English preferred)
                            descriptions = cve_data.get("descriptions", [])
                            description = ""
                            for desc in descriptions:
                                if desc.get("lang") == "en":
                                    description = desc.get("value", "")
                                    break
                            if not description and descriptions:
                                description = descriptions[0].get("value", "")
                            
                            # Extract CVSS scores
                            metrics = cve_data.get("metrics", {})
                            cvss_v3_score = None
                            cvss_v3_severity = None
                            cvss_v2_score = None
                            
                            if "cvssMetricV31" in metrics and metrics["cvssMetricV31"]:
                                cvss_v3_score = metrics["cvssMetricV31"][0].get("cvssData", {}).get("baseScore")
                                cvss_v3_severity = metrics["cvssMetricV31"][0].get("cvssData", {}).get("baseSeverity")
                            elif "cvssMetricV30" in metrics and metrics["cvssMetricV30"]:
                                cvss_v3_score = metrics["cvssMetricV30"][0].get("cvssData", {}).get("baseScore")
                                cvss_v3_severity = metrics["cvssMetricV30"][0].get("cvssData", {}).get("baseSeverity")
                            
                            if "cvssMetricV2" in metrics and metrics["cvssMetricV2"]:
                                cvss_v2_score = metrics["cvssMetricV2"][0].get("cvssData", {}).get("baseScore")
                            
                            # Store raw data as JSONB
                            raw_data = json.dumps(cve_data)
                            
                            try:
                                await conn.execute("""
                                    INSERT INTO nvd_vulnerabilities 
                                    (job_id, cve_id, source_identifier, published, last_modified, 
                                     vuln_status, description, cvss_v3_score, cvss_v3_severity, 
                                     cvss_v2_score, raw_data)
                                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                                    ON CONFLICT (job_id, cve_id) DO UPDATE SET
                                        last_modified = EXCLUDED.last_modified,
                                        vuln_status = EXCLUDED.vuln_status,
                                        cvss_v3_score = EXCLUDED.cvss_v3_score,
                                        cvss_v3_severity = EXCLUDED.cvss_v3_severity,
                                        raw_data = EXCLUDED.raw_data
                                """, job_id, cve_id, source_id, published, last_modified,
                                     vuln_status, description, cvss_v3_score, cvss_v3_severity,
                                     cvss_v2_score, raw_data)
                            except Exception as e:
                                logger.warning(f"Error saving vulnerability {cve_id}: {e}")
                    
                    logger.info(f"Saved job {job_id} with {len(job.get('vulnerabilities', []))} vulnerabilities")
    
    async def get_all_jobs(self) -> List[Dict[str, Any]]:
        """Get all jobs from PostgreSQL"""
        if not self._pool:
            await self.connect()
        
        async with self._pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT j.*, 
                       COUNT(v.id) as vulnerabilities_count,
                       json_agg(
                           json_build_object(
                               'cve', v.raw_data::json
                           )
                       ) FILTER (WHERE v.id IS NOT NULL) as vulnerabilities
                FROM nvd_jobs j
                LEFT JOIN nvd_vulnerabilities v ON j.job_id = v.job_id
                GROUP BY j.id
                ORDER BY j.processed_at DESC
            """)
            
            results = []
            for row in rows:
                job = dict(row)
                # Convert datetime to timestamp for compatibility
                if job.get("processed_at"):
                    job["processed_at"] = job["processed_at"].timestamp()
                if job.get("created_at"):
                    job["created_at"] = job["created_at"].isoformat()
                if job.get("updated_at"):
                    job["updated_at"] = job["updated_at"].isoformat()
                
                # Parse vulnerabilities JSON
                if job.get("vulnerabilities"):
                    try:
                        if isinstance(job["vulnerabilities"], str):
                            job["vulnerabilities"] = json.loads(job["vulnerabilities"])
                    except:
                        job["vulnerabilities"] = []
                else:
                    job["vulnerabilities"] = []
                
                results.append(job)
            
            return results
    
    async def get_jobs_by_keyword(self, keyword: str) -> List[Dict[str, Any]]:
        """Get jobs by keyword from PostgreSQL"""
        if not self._pool:
            await self.connect()
        
        async with self._pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT j.*, 
                       COUNT(v.id) as vulnerabilities_count,
                       json_agg(
                           json_build_object(
                               'cve', v.raw_data::json
                           )
                       ) FILTER (WHERE v.id IS NOT NULL) as vulnerabilities
                FROM nvd_jobs j
                LEFT JOIN nvd_vulnerabilities v ON j.job_id = v.job_id
                WHERE j.keyword = $1
                GROUP BY j.id
                ORDER BY j.processed_at DESC
            """, keyword)
            
            results = []
            for row in rows:
                job = dict(row)
                if job.get("processed_at"):
                    job["processed_at"] = job["processed_at"].timestamp()
                    job["processed_at_readable"] = datetime.fromtimestamp(
                        job["processed_at"]
                    ).strftime("%Y-%m-%d %H:%M:%S")
                
                if job.get("vulnerabilities"):
                    try:
                        if isinstance(job["vulnerabilities"], str):
                            job["vulnerabilities"] = json.loads(job["vulnerabilities"])
                    except:
                        job["vulnerabilities"] = []
                else:
                    job["vulnerabilities"] = []
                
                results.append(job)
            
            return results
    
    def _parse_datetime(self, date_str) -> Optional[datetime]:
        """Convert date string to datetime object"""
        if not date_str:
            return None
        
        try:
            if isinstance(date_str, str):
                return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            elif isinstance(date_str, datetime):
                return date_str
            else:
                return None
        except Exception:
            return None
