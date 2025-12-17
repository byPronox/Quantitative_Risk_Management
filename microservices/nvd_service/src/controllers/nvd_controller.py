"""
NVD Controller - Complete API endpoints for vulnerability data and Database operations.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, Dict, Any, List
import logging
from datetime import datetime

# Import services
from ..services.nvd_service import NVDService
from ..services.database_service import DatabaseService
from ..services.queue_service import QueueService
from ..services.risk_analysis_service import RiskAnalysisService

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize services
nvd_service = NVDService()
database_service = DatabaseService()
queue_service = QueueService()
risk_service = RiskAnalysisService()

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check NVD service
        nvd_healthy = await nvd_service.health_check()
        
        # Check queue service
        queue_healthy = queue_service.health_check()
        
        services = {
            "nvd_api": "healthy" if nvd_healthy else "unhealthy",
            "queue": "healthy" if queue_healthy else "unhealthy",
            "risk_analysis": "healthy"  # Always healthy as it's computational
        }
        
        overall_status = "healthy" if all(s == "healthy" for s in services.values()) else "degraded"
        
        return {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "services": services,
            "version": "1.0.0"
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Health check failed: {str(e)}")

@router.get("/vulnerabilities/search")
async def search_vulnerabilities(
    keyword: Optional[str] = Query(None, description="Search keyword"),
    cve_id: Optional[str] = Query(None, description="Specific CVE ID"),
    cpe_name: Optional[str] = Query(None, description="CPE name filter"),
    results_per_page: int = Query(default=20, ge=1, le=100),
    start_index: int = Query(default=0, ge=0)
):
    """Search for vulnerabilities using NVD API"""
    try:
        result = await nvd_service.search_vulnerabilities(
            keywords=keyword,
            cve_id=cve_id,
            cpe_name=cpe_name,
            results_per_page=results_per_page,
            start_index=start_index
        )
        
        return result
    except Exception as e:
        logger.error(f"Vulnerability search failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.get("/vulnerabilities/{cve_id}")
async def get_vulnerability(cve_id: str):
    """Get a specific vulnerability by CVE ID"""
    try:
        result = await nvd_service.get_vulnerability(cve_id)
        if not result:
            raise HTTPException(status_code=404, detail=f"CVE {cve_id} not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get vulnerability {cve_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get vulnerability: {str(e)}")

# Database endpoints
@router.get("/database/results/all")
async def get_all_database_results():
    """Get all Database results (jobs with vulnerabilities)"""
    try:
        results = await database_service.get_all_jobs()
        return {
            "success": True,
            "total_jobs": len(results),
            "jobs": results
        }
    except Exception as e:
        logger.error("Error getting all Database results: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/database/jobs")
async def get_all_jobs():
    """Get all jobs from nvd_jobs table"""
    try:
        results = await database_service.get_all_jobs()
        return {
            "success": True,
            "total_jobs": len(results),
            "jobs": results
        }
    except Exception as e:
        logger.error("Error getting all jobs: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/database/vulnerabilities")
async def get_all_vulnerabilities(
    limit: Optional[int] = Query(None, ge=1, le=1000, description="Maximum number of vulnerabilities to return"),
    offset: int = Query(0, ge=0, description="Number of vulnerabilities to skip")
):
    """Get all vulnerabilities from nvd_vulnerabilities table"""
    try:
        results = await database_service.get_all_vulnerabilities(limit=limit, offset=offset)
        return {
            "success": True,
            "total_vulnerabilities": len(results),
            "vulnerabilities": results
        }
    except Exception as e:
        logger.error("Error getting all vulnerabilities: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/database/vulnerabilities/job/{job_id}")
async def get_vulnerabilities_by_job(job_id: str):
    """Get all vulnerabilities for a specific job_id"""
    try:
        results = await database_service.get_vulnerabilities_by_job_id(job_id)
        return {
            "success": True,
            "job_id": job_id,
            "total_vulnerabilities": len(results),
            "vulnerabilities": results
        }
    except Exception as e:
        logger.error("Error getting vulnerabilities for job %s: %s", job_id, str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/database/reports/keywords")
async def get_database_keyword_reports():
    """Get keyword-based reports from Database"""
    try:
        reports = await database_service.get_reports_by_keywords()
        return {
            "success": True,
            "keywords": reports,
            "total_keywords": len(reports)
        }
    except Exception as e:
        logger.error(f"Failed to get keyword reports: {str(e)}")
        return {
            "success": False,
            "error": f"Failed to get keyword reports: {str(e)}",
            "keywords": []
        }

@router.post("/database/save")
async def save_to_database(data: Dict[str, Any]):
    """Save data to Database"""
    try:
        await database_service.save_job_results([data])
        return {"success": True, "message": "Data saved to Database"}
    except Exception as e:
        logger.error(f"Failed to save to Database: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to save to Database: {str(e)}")

# Queue endpoints
@router.post("/queue/job")
async def add_queue_job(
    keyword: str = Query(..., description="Search keyword"),
    metadata: Optional[Dict[str, Any]] = None
):
    """Add a job to the queue"""
    try:
        if metadata is None:
            metadata = {}
        job_id = await queue_service.add_job(keyword, metadata)
        return {
            "job_id": job_id,
            "status": "queued",
            "keyword": keyword,
            "message": "Job added to queue"
        }
    except Exception as e:
        logger.error(f"Failed to add job to queue: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to add job to queue: {str(e)}")

@router.post("/analyze_software_async")
async def analyze_software_async(request_data: Dict[str, Any]):
    """Analyze multiple software packages asynchronously"""
    try:
        software_list = request_data.get("software_list", [])
        metadata = request_data.get("metadata", {})
        
        if not software_list:
            raise HTTPException(status_code=400, detail="Software list is required")
        
        # Create jobs for each software package
        job_ids = []
        for software in software_list:
            job_id = await queue_service.add_job(software, metadata)
            job_ids.append(job_id)
        
        return {
            "success": True,
            "message": f"Added {len(software_list)} jobs to analysis queue",
            "job_ids": job_ids,
            "estimated_time": len(software_list) * 30,  # Estimate 30 seconds per job
            "software_count": len(software_list)
        }
    except Exception as e:
        logger.error(f"Failed to analyze software async: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze software async: {str(e)}")

@router.get("/queue/job/{job_id}")
async def get_queue_job(job_id: str):
    """Get a specific job by ID"""
    try:
        result = queue_service.get_job_result(job_id)
        if not result:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get job: {str(e)}")

@router.get("/results/{job_id}")
async def get_job_results_frontend(job_id: str):
    """Get job results (Frontend compatibility endpoint)"""
    return await get_queue_job(job_id)

@router.get("/queue/results/all")
async def get_all_queue_results():
    """Get all queue job results"""
    try:
        results = queue_service.get_all_job_results()
        return results
    except Exception as e:
        logger.error(f"Failed to get queue results: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get queue results: {str(e)}")

@router.get("/queue/status")
async def get_queue_status():
    """Get queue status"""
    try:
        status = queue_service.peek_queue_status()
        return status
    except Exception as e:
        logger.error(f"Failed to get queue status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get queue status: {str(e)}")

@router.post("/queue/consumer/start")
async def start_queue_consumer():
    """Start the queue consumer"""
    try:
        result = queue_service.start_consumer()
        return result
    except Exception as e:
        logger.error(f"Failed to start consumer: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start consumer: {str(e)}")

@router.post("/queue/consumer/stop")
async def stop_queue_consumer():
    """Stop the queue consumer"""
    try:
        result = queue_service.stop_consumer()
        return result
    except Exception as e:
        logger.error(f"Failed to stop consumer: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to stop consumer: {str(e)}")

@router.get("/queue/jobs")
async def get_all_queue_jobs():
    """Get all jobs with their status (pending, processing, completed)"""
    try:
        jobs = queue_service.get_all_job_results()
        return jobs
    except Exception as e:
        logger.error(f"Failed to get all queue jobs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get all queue jobs: {str(e)}")

# Risk analysis endpoints
@router.post("/risk/analyze")
async def analyze_risk():
    """Analyze risks from queue data"""
    try:
        # Get vulnerability data from queue
        vulnerability_data = queue_service.get_all_vulnerability_data()
        
        if not vulnerability_data:
            return {"message": "No vulnerability data available for analysis"}
        
        # Analyze risks
        risk_analysis = risk_service.analyze_vulnerability_risks(vulnerability_data)
        
        return {
            "risk_analysis": risk_analysis,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Risk analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Risk analysis failed: {str(e)}")

@router.post("/risk/enterprise")
async def get_enterprise_metrics():
    """Get enterprise risk metrics"""
    try:
        # Get vulnerability data from queue
        vulnerability_data = queue_service.get_all_vulnerability_data()
        
        if not vulnerability_data:
            return {"error": "No vulnerability data available for analysis"}
        
        # Calculate enterprise metrics
        enterprise_metrics = risk_service.calculate_enterprise_metrics(vulnerability_data)
        
        return enterprise_metrics
    except Exception as e:
        logger.error(f"Enterprise metrics calculation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Enterprise metrics calculation failed: {str(e)}")

@router.get("/metrics")
async def get_service_metrics():
    """Get service metrics"""
    try:
        metrics = queue_service.get_metrics()
        
        return {
            "service_name": "nvd_service",
            "uptime_seconds": metrics.get("uptime_seconds", 0),
            "total_requests": metrics.get("total_requests", 0),
            "successful_requests": metrics.get("successful_requests", 0),
            "failed_requests": metrics.get("failed_requests", 0),
            "average_response_time": metrics.get("average_response_time", 0.0),
            "queue_size": metrics.get("queue_size", 0),
            "active_jobs": metrics.get("active_jobs", 0),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")


@router.post("/consumer/stop")
async def stop_consumer():
    """Stop the queue consumer"""
    try:
        result = queue_service.stop_consumer()
        return result
    except Exception as e:
        logger.error("Error stopping consumer: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# LEGACY ENDPOINTS (for backward compatibility)
# =============================================================================

@router.get("/results/all")
async def get_all_results_legacy():
    """Get all NVD analysis results (legacy endpoint)"""
    try:
        results = queue_service.get_all_job_results()
        return results
    except Exception as e:
        logger.error("Error getting all results: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# MONGODB ENDPOINTS (New refactored endpoints)
# =============================================================================

@router.get("/database/results/{keyword}")
async def get_database_results_by_keyword(keyword: str):
    """Get NVD analysis results by keyword from Database"""
    try:
        results = await database_service.get_detailed_report_by_keyword(keyword)
        return results
    except Exception as e:
        logger.error("Error getting Database results for keyword %s: %s", keyword, str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/database/reports/detailed/{keyword}")
async def get_database_detailed_report(keyword: str):
    """Get detailed vulnerability report for a specific keyword from Database"""
    try:
        report = await database_service.get_detailed_report_by_keyword(keyword)
        return report
    except Exception as e:
        logger.error("Error getting Database detailed report for %s: %s", keyword, str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/database/analyze")
async def analyze_cves_with_database(
    keywords: List[str],
    max_results: int = Query(default=100, ge=1, le=1000)
):
    """Analyze CVEs for given keywords and save to Database"""
    try:
        # For now, this is a placeholder - we'll need to implement the actual analysis
        # This would typically interface with the NVD API and then save to Database
        return {
            "success": True,
            "message": f"Analysis requested for {len(keywords)} keywords",
            "keywords": keywords,
            "max_results": max_results
        }
    except Exception as e:
        logger.error("Error analyzing CVEs with Database: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/database/health")
async def check_database_health():
    """Check Database connection health"""
    try:
        await database_service.connect()
        await database_service.disconnect()
        return {
            "success": True,
            "message": "Database connection healthy",
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        logger.error("Database health check failed: %s", str(e))
        return {
            "success": False,
            "message": f"Database connection failed: {str(e)}",
            "timestamp": datetime.utcnow()
        }
