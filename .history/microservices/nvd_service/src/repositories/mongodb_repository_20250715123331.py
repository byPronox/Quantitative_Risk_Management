"""
MongoDB Repository for NVD service
"""
import logging
from typing import List, Dict, Any
from datetime import datetime
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor
from ..config.settings import settings

logger = logging.getLogger(__name__)


class MongoDBRepository:
    """Repository for MongoDB operations in NVD microservice"""
    
    def __init__(self):
        self.client = None
        self.db = None
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    async def connect(self):
        """Connect to MongoDB Atlas"""
        try:
            from pymongo import MongoClient
            
            # Use the same MongoDB Atlas configuration as report service
            mongodb_url = os.getenv("MONGODB_URL", "mongodb+srv://ADMIN:ADMIN@cluster0.7ixig65.mongodb.net/")
            self.client = MongoClient(mongodb_url)
            self.db = self.client.cveScanner
            
            # Test connection
            await asyncio.get_event_loop().run_in_executor(
                self.executor, self.client.admin.command, 'ping'
            )
            logger.info("MongoDB connection established")
            
        except Exception as e:
            logger.error("Failed to connect to MongoDB: %s", str(e))
            raise
    
    async def disconnect(self):
        """Disconnect from MongoDB"""
        if self.client:
            await asyncio.get_event_loop().run_in_executor(
                self.executor, self.client.close
            )
            logger.info("MongoDB connection closed")
    
    def _save_jobs_sync(self, jobs_data: List[Dict[str, Any]]):
        """Synchronous version of save_jobs"""
        for job in jobs_data:
            if job.get("status") == "completed" and job.get("vulnerabilities"):
                # Convert structure for MongoDB schema
                job_document = {
                    "job_id": job.get("job_id", ""),
                    "keyword": job.get("keyword", ""),
                    "status": job.get("status", "pending"),
                    "total_results": int(job.get("total_results", 0)),
                    "processed_at": float(job.get("timestamp", time.time())),
                    "processed_via": job.get("processed_via", "nvd_microservice"),
                    "vulnerabilities": []
                }
                
                # Process each vulnerability
                for vuln in job.get("vulnerabilities", []):
                    if "cve" in vuln:
                        cve_data = vuln["cve"]
                        processed_vuln = {
                            "cve": {
                                "id": cve_data.get("id", ""),
                                "sourceIdentifier": cve_data.get("sourceIdentifier", ""),
                                "published": self._convert_to_datetime(cve_data.get("published")),
                                "lastModified": self._convert_to_datetime(cve_data.get("lastModified")),
                                "vulnStatus": cve_data.get("vulnStatus", "Unknown"),
                                "cveTags": cve_data.get("cveTags", []),
                                "descriptions": cve_data.get("descriptions", []),
                                "metrics": cve_data.get("metrics", {}),
                                "weaknesses": cve_data.get("weaknesses", []),
                                "configurations": cve_data.get("configurations", []),
                                "references": cve_data.get("references", []),
                                "vendorComments": cve_data.get("vendorComments", [])
                            }
                        }
                        job_document["vulnerabilities"].append(processed_vuln)
                
                # Insert or update in MongoDB (upsert by job_id)
                self.db.jobs.update_one(
                    {"job_id": job_document["job_id"]},
                    {"$set": job_document},
                    upsert=True
                )
                
                logger.info("Saved job %s with %d vulnerabilities to MongoDB", 
                          job_document['job_id'], len(job_document['vulnerabilities']))
    
    async def save_jobs(self, jobs_data: List[Dict[str, Any]]):
        """Save job results to MongoDB"""
        if not self.client:
            await self.connect()
        
        try:
            await asyncio.get_event_loop().run_in_executor(
                self.executor, self._save_jobs_sync, jobs_data
            )
            
        except Exception as e:
            logger.error("Error saving job results to MongoDB: %s", str(e))
            raise
    
    def _get_all_jobs_sync(self):
        """Synchronous version of get_all_jobs"""
        cursor = self.db.jobs.find({}).sort("processed_at", -1)
        results = []
        
        for doc in cursor:
            # Convert ObjectId to string for JSON serialization
            doc["_id"] = str(doc["_id"])
            
            # Convert datetime to timestamp for compatibility
            if "processed_at" in doc and isinstance(doc["processed_at"], datetime):
                doc["processed_at"] = doc["processed_at"].timestamp()
            
            results.append(doc)
        
        return results
    
    async def get_all_jobs(self) -> List[Dict[str, Any]]:
        """Get all jobs from MongoDB"""
        if not self.client:
            await self.connect()
        
        try:
            results = await asyncio.get_event_loop().run_in_executor(
                self.executor, self._get_all_jobs_sync
            )
            return results
            
        except Exception as e:
            logger.error("Error getting all jobs from MongoDB: %s", str(e))
            raise
    
    def _get_jobs_by_keyword_sync(self, keyword: str):
        """Synchronous version of get_jobs_by_keyword"""
        cursor = self.db.jobs.find({"keyword": keyword}).sort("processed_at", -1)
        jobs = []
        
        for job in cursor:
            # Convert ObjectId to string for JSON serialization
            job["_id"] = str(job["_id"])
            
            # Convert processed_at to readable format
            processed_at = job.get("processed_at")
            if isinstance(processed_at, (int, float)):
                job["processed_at_readable"] = datetime.fromtimestamp(processed_at).strftime("%Y-%m-%d %H:%M:%S")
            
            jobs.append(job)
        
        return jobs
    
    async def get_jobs_by_keyword(self, keyword: str) -> List[Dict[str, Any]]:
        """Get jobs by keyword from MongoDB"""
        if not self.client:
            await self.connect()
        
        try:
            jobs = await asyncio.get_event_loop().run_in_executor(
                self.executor, self._get_jobs_by_keyword_sync, keyword
            )
            return jobs
            
        except Exception as e:
            logger.error("Error getting jobs by keyword from MongoDB: %s", str(e))
            raise
    
    def _convert_to_datetime(self, date_str):
        """Convert date string to datetime object"""
        if not date_str:
            return datetime(1970, 1, 1)
        
        try:
            # Handle ISO format with Z
            if isinstance(date_str, str):
                return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            elif isinstance(date_str, datetime):
                return date_str
            else:
                return datetime(1970, 1, 1)
        except Exception:
            return datetime(1970, 1, 1)
