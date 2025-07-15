"""
MongoDB service for NVD microservice
"""
import logging
from typing import List, Dict, Any
from datetime import datetime
import time
import os
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)


class MongoDBService:
    """Service for MongoDB operations in NVD microservice"""
    
    def __init__(self):
        self.client = None
        self.db = None
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    async def connect(self):
        """Connect to MongoDB"""
        try:
            from pymongo import MongoClient
            
            mongodb_url = os.getenv("MONGODB_URL", "mongodb://admin:admin123@mongodb:27017/quantitative_risk_management?authSource=admin")
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
        finally:
            await self.disconnect()
    
    def _save_job_results_sync(self, jobs_data: List[Dict[str, Any]]):
        """Synchronous version of save_job_results"""
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
    
    async def save_job_results(self, jobs_data: List[Dict[str, Any]]):
        """Save job results to MongoDB"""
        if not self.client:
            await self.connect()
        
        try:
            await asyncio.get_event_loop().run_in_executor(
                self.executor, self._save_job_results_sync, jobs_data
            )
            
        except Exception as e:
            logger.error("Error saving job results to MongoDB: %s", str(e))
            raise
        finally:
            await self.disconnect()
    
    def _get_reports_by_keywords_sync(self):
        """Synchronous version of get_reports_by_keywords"""
        cursor = self.db.jobs.find({}).sort("processed_at", -1)
        jobs_by_keyword = {}
        
        for job in cursor:
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
                "vulnerabilities_count": len(job.get("vulnerabilities", [])),
                "processed_at": processed_at_readable,
                "processed_at_timestamp": processed_at
            }
            
            jobs_by_keyword[keyword]["jobs"].append(job_summary)
            jobs_by_keyword[keyword]["total_jobs"] += 1
            jobs_by_keyword[keyword]["total_vulnerabilities"] += job_summary["vulnerabilities_count"]
            
            # Update latest analysis
            if (jobs_by_keyword[keyword]["latest_analysis"] is None or 
                processed_at > jobs_by_keyword[keyword]["latest_analysis"]):
                jobs_by_keyword[keyword]["latest_analysis"] = processed_at_readable
        
        # Convert to list and sort by total vulnerabilities
        keywords_list = list(jobs_by_keyword.values())
        keywords_list.sort(key=lambda x: x["total_vulnerabilities"], reverse=True)
        
        return keywords_list
    
    async def get_reports_by_keywords(self) -> List[Dict[str, Any]]:
        """Get vulnerability data grouped by keywords"""
        if not self.client:
            await self.connect()
        
        try:
            keywords_list = await asyncio.get_event_loop().run_in_executor(
                self.executor, self._get_reports_by_keywords_sync
            )
            return keywords_list
            
        except Exception as e:
            logger.error("Error getting reports by keywords: %s", str(e))
            raise
        finally:
            await self.disconnect()
    
    def _get_detailed_report_by_keyword_sync(self, keyword: str):
        """Synchronous version of get_detailed_report_by_keyword"""
        cursor = self.db.jobs.find({"keyword": keyword}).sort("processed_at", -1)
        jobs = []
        all_vulnerabilities = []
        total_vulnerabilities = 0
        
        for job in cursor:
            # Convert ObjectId to string for JSON serialization
            job["_id"] = str(job["_id"])
            
            # Convert processed_at to readable format
            processed_at = job.get("processed_at")
            if isinstance(processed_at, (int, float)):
                job["processed_at_readable"] = datetime.fromtimestamp(processed_at).strftime("%Y-%m-%d %H:%M:%S")
            
            # Add vulnerabilities to the complete list
            vulnerabilities = job.get("vulnerabilities", [])
            all_vulnerabilities.extend(vulnerabilities)
            total_vulnerabilities += len(vulnerabilities)
            
            jobs.append(job)
        
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
                        # If it's a datetime object, extract year
                        year = str(published.year) if hasattr(published, 'year') else str(published)[:4]
                    cve_years[year] = cve_years.get(year, 0) + 1
                except Exception:
                    # If any error, skip this entry
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
    
    async def get_detailed_report_by_keyword(self, keyword: str) -> Dict[str, Any]:
        """Get detailed vulnerability report for a specific keyword"""
        if not self.client:
            await self.connect()
        
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                self.executor, self._get_detailed_report_by_keyword_sync, keyword
            )
            return result
            
        except Exception as e:
            logger.error("Error getting detailed report for keyword %s: %s", keyword, str(e))
            raise
        finally:
            await self.disconnect()
    
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
