"""
Database Service for NVD microservice using PostgreSQL/Supabase
Replaces MongoDB service with clean architecture
"""
import logging
from typing import List, Dict, Any
from datetime import datetime
import time

from ..repositories.postgres_repository import PostgresRepository

logger = logging.getLogger(__name__)


class DatabaseService:
    """Service for PostgreSQL/Supabase operations in NVD microservice"""
    
    def __init__(self):
        self.repository = PostgresRepository()
    
    async def connect(self):
        """Connect to PostgreSQL"""
        try:
            await self.repository.connect()
            logging.info("DatabaseService: Conexión exitosa a PostgreSQL/Supabase.")
        except Exception as e:
            logging.error(f"DatabaseService: Error al conectar a PostgreSQL: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from PostgreSQL"""
        await self.repository.disconnect()
    
    async def save_job_results(self, jobs_data: List[Dict[str, Any]]):
        """Save job results to PostgreSQL"""
        try:
            await self.repository.save_jobs(jobs_data)
            logging.info(f"DatabaseService: Resultados guardados en PostgreSQL. Total: {len(jobs_data) if isinstance(jobs_data, list) else 1}")
        except Exception as e:
            logging.error(f"DatabaseService: Error al guardar resultados: {e}")
            raise
    
    async def get_all_jobs(self) -> List[Dict[str, Any]]:
        """Get all jobs from PostgreSQL"""
        return await self.repository.get_all_jobs()
    
    async def get_reports_by_keywords(self) -> List[Dict[str, Any]]:
        """Get vulnerability data grouped by keywords"""
        try:
            all_jobs = await self.repository.get_all_jobs()
            jobs_by_keyword = {}
            
            for job in all_jobs:
                keyword = job.get("keyword", "Unknown")
                if keyword not in jobs_by_keyword:
                    jobs_by_keyword[keyword] = {
                        "keyword": keyword,
                        "total_jobs": 0,
                        "total_vulnerabilities": 0,
                        "latest_analysis": None,
                        "jobs": []
                    }
                
                # Convert processed_at to readable format
                processed_at = job.get("processed_at")
                if isinstance(processed_at, (int, float)):
                    processed_at_readable = datetime.fromtimestamp(processed_at).strftime("%Y-%m-%d %H:%M:%S")
                else:
                    processed_at_readable = str(processed_at)
                
                job_summary = {
                    "job_id": job.get("job_id"),
                    "status": job.get("status"),
                    "total_results": job.get("total_results", 0),
                    "vulnerabilities_count": job.get("vulnerabilities_count", len(job.get("vulnerabilities", []))),
                    "processed_at": processed_at_readable,
                    "processed_at_timestamp": processed_at
                }
                
                jobs_by_keyword[keyword]["jobs"].append(job_summary)
                jobs_by_keyword[keyword]["total_jobs"] += 1
                jobs_by_keyword[keyword]["total_vulnerabilities"] += job_summary["vulnerabilities_count"]
                
                # Update latest analysis
                if (jobs_by_keyword[keyword]["latest_analysis"] is None or 
                    (isinstance(processed_at, (int, float)) and 
                     isinstance(jobs_by_keyword[keyword]["latest_analysis"], str)) or
                    (isinstance(processed_at, (int, float)) and 
                     isinstance(jobs_by_keyword[keyword]["latest_analysis"], (int, float)) and
                     processed_at > jobs_by_keyword[keyword]["latest_analysis"])):
                    jobs_by_keyword[keyword]["latest_analysis"] = processed_at_readable
            
            # Convert to list and sort by total vulnerabilities
            keywords_list = list(jobs_by_keyword.values())
            keywords_list.sort(key=lambda x: x["total_vulnerabilities"], reverse=True)
            
            return keywords_list
            
        except Exception as e:
            logger.error("Error getting reports by keywords: %s", str(e))
            raise
    
    async def get_detailed_report_by_keyword(self, keyword: str) -> Dict[str, Any]:
        """Get detailed vulnerability report for a specific keyword"""
        try:
            jobs = await self.repository.get_jobs_by_keyword(keyword)
            all_vulnerabilities = []
            total_vulnerabilities = 0
            
            for job in jobs:
                vulnerabilities = job.get("vulnerabilities", [])
                all_vulnerabilities.extend(vulnerabilities)
                total_vulnerabilities += len(vulnerabilities)
            
            # Analyze vulnerability severity distribution
            severity_stats = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0, "Unknown": 0}
            cve_years = {}
            
            for vuln in all_vulnerabilities:
                # Count by severity
                metrics = vuln.get("cve", {}).get("metrics", {})
                severity = "Unknown"
                
                if "cvssMetricV31" in metrics and metrics["cvssMetricV31"]:
                    severity = metrics["cvssMetricV31"][0].get("cvssData", {}).get("baseSeverity", "Unknown")
                elif "cvssMetricV2" in metrics and metrics["cvssMetricV2"]:
                    score = metrics["cvssMetricV2"][0].get("cvssData", {}).get("baseScore", 0)
                    if score >= 9.0:
                        severity = "Critical"
                    elif score >= 7.0:
                        severity = "High"
                    elif score >= 4.0:
                        severity = "Medium"
                    else:
                        severity = "Low"
                
                severity_stats[severity] = severity_stats.get(severity, 0) + 1
                
                # Count by year
                published = vuln.get("cve", {}).get("published", "")
                if published:
                    try:
                        if isinstance(published, str):
                            year = published[:4]
                        else:
                            year = str(published.year) if hasattr(published, 'year') else str(published)[:4]
                        cve_years[year] = cve_years.get(year, 0) + 1
                    except Exception:
                        pass
            
            return {
                "success": True,
                "keyword": keyword,
                "total_jobs": len(jobs),
                "total_vulnerabilities": total_vulnerabilities,
                "severity_distribution": severity_stats,
                "vulnerabilities_by_year": dict(sorted(cve_years.items(), reverse=True)),
                "jobs": jobs,
                "vulnerabilities": all_vulnerabilities
            }
            
        except Exception as e:
            logger.error("Error getting detailed report for keyword %s: %s", keyword, str(e))
            raise


# Alias for backward compatibility
MongoDBService = DatabaseService
