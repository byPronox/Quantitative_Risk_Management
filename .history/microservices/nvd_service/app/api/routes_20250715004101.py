from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query, Request
from typing import Optional, Dict, Any
import uuid
import logging
from datetime import datetime

from app.api.schemas import (
    VulnerabilitySearchRequest,
    VulnerabilitySearchResponse,
    RiskAnalysisRequest,
    RiskAnalysisResponse,
    QueueJobRequest,
    QueueJobResponse,
    QueueJobStatus,
    ServiceMetrics,
    HealthResponse
)
from app.services.nvd_service import NVDService
from app.services.risk_analysis_service import RiskAnalysisService
from app.services.queue_service import QueueService

router = APIRouter()
logger = logging.getLogger(__name__)

# Service instances - these would be dependency injected in production
nvd_service = NVDService()
risk_service = RiskAnalysisService()
queue_service = QueueService()


@router.get("/health", response_model=HealthResponse)
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
        
        return HealthResponse(
            status=overall_status,
            timestamp=datetime.utcnow(),
            services=services,
            version="1.0.0"
        )
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Health check failed: {str(e)}")


@router.get("/metrics", response_model=ServiceMetrics)
async def get_metrics():
    """Get service metrics"""
    try:
        metrics = queue_service.get_metrics()
        
        return ServiceMetrics(
            service_name="nvd_service",
            uptime_seconds=metrics.get("uptime_seconds", 0),
            total_requests=metrics.get("total_requests", 0),
            successful_requests=metrics.get("successful_requests", 0),
            failed_requests=metrics.get("failed_requests", 0),
            average_response_time=metrics.get("average_response_time", 0.0),
            queue_size=metrics.get("queue_size", 0),
            active_jobs=metrics.get("active_jobs", 0),
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")


@router.post("/vulnerabilities/search")
async def search_vulnerabilities(request: VulnerabilitySearchRequest):
    """Search for vulnerabilities using NVD API"""
    try:
        result = await nvd_service.search_vulnerabilities(
            keywords=request.keywords,
            cve_id=request.cve_id,
            cpe_name=request.cpe_name,
            results_per_page=request.results_per_page,
            start_index=request.start_index,
            pub_start_date=request.pub_start_date,
            pub_end_date=request.pub_end_date,
            last_mod_start_date=request.last_mod_start_date,
            last_mod_end_date=request.last_mod_end_date
        )
        
        # Return raw result without Pydantic validation for now
        # TODO: Transform NVD API response to match our schema
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/vulnerabilities/search")
async def search_vulnerabilities_get(
    keywords: str = Query(default=None, description="Keywords to search for"),
    results_per_page: int = Query(default=20, ge=1, le=2000),
    cve_id: str = Query(default=None),
    cpe_name: str = Query(default=None),
    start_index: int = Query(default=0, ge=0),
    pub_start_date: str = Query(default=None),
    pub_end_date: str = Query(default=None),
    last_mod_start_date: str = Query(default=None),
    last_mod_end_date: str = Query(default=None)
):
    """Search for vulnerabilities using NVD API (GET version)"""
    try:
        result = await nvd_service.search_vulnerabilities(
            keywords=keywords,
            cve_id=cve_id,
            cpe_name=cpe_name,
            results_per_page=results_per_page,
            start_index=start_index,
            pub_start_date=pub_start_date,
            pub_end_date=pub_end_date,
            last_mod_start_date=last_mod_start_date,
            last_mod_end_date=last_mod_end_date
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/vulnerabilities/{cve_id}")
async def get_vulnerability(cve_id: str):
    """Get specific vulnerability by CVE ID"""
    try:
        result = await nvd_service.get_vulnerability(cve_id)
        if not result:
            raise HTTPException(status_code=404, detail=f"CVE {cve_id} not found")
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get vulnerability: {str(e)}")


@router.post("/analysis/risk", response_model=RiskAnalysisResponse)
async def analyze_risk(request: RiskAnalysisRequest):
    """Perform risk analysis on vulnerabilities"""
    try:
        # First, get vulnerability details from NVD
        vulnerabilities_data = []
        for cve_id in request.vulnerabilities:
            vuln_data = await nvd_service.get_vulnerability(cve_id)
            if vuln_data:
                vulnerabilities_data.append(vuln_data)
        
        if not vulnerabilities_data:
            raise HTTPException(status_code=404, detail="No valid vulnerabilities found")
        
        # Perform risk analysis
        result = risk_service.analyze_risk(
            vulnerabilities_data,
            asset_criticality=request.asset_criticality,
            threat_landscape=request.threat_landscape
        )
        
        return RiskAnalysisResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Risk analysis failed: {str(e)}")


@router.post("/queue/jobs", response_model=QueueJobResponse)
async def queue_job(request: QueueJobRequest, background_tasks: BackgroundTasks):
    """Queue a job for background processing"""
    try:
        job_id = str(uuid.uuid4())
        
        # Queue the job
        success = queue_service.queue_job(
            job_id=job_id,
            job_type=request.job_type,
            parameters=request.parameters,
            priority=request.priority,
            callback_url=request.callback_url
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to queue job")
        
        # Add background task to process the job
        background_tasks.add_task(process_background_job, job_id, request)
        
        return QueueJobResponse(
            job_id=job_id,
            status="queued",
            created_at=datetime.utcnow()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to queue job: {str(e)}")


@router.get("/queue/jobs/{job_id}", response_model=QueueJobStatus)
async def get_job_status(job_id: str):
    """Get status of a queued job"""
    try:
        status = queue_service.get_job_status(job_id)
        if not status:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return QueueJobStatus(**status)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get job status: {str(e)}")


@router.delete("/queue/jobs/{job_id}")
async def cancel_job(job_id: str):
    """Cancel a queued job"""
    try:
        success = queue_service.cancel_job(job_id)
        if not success:
            raise HTTPException(status_code=404, detail="Job not found or cannot be cancelled")
        
        return {"message": f"Job {job_id} cancelled successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel job: {str(e)}")


# --- Cola de análisis NVD ---
@router.get("/queue/status")
async def get_queue_status():
    """Get RabbitMQ queue status for NVD analysis"""
    try:
        queue_info = queue_service.peek_queue_status()
        return queue_info
    except Exception as e:
        return {
            "error": str(e),
            "connected": False,
            "queue_size": 0,
            "total_vulnerabilities": 0,
            "keywords": []
        }


@router.delete("/queue/clear")
async def clear_queue():
    """Clear the RabbitMQ queue"""
    try:
        result = queue_service.clear_queue()
        return {
            "message": "Queue cleared successfully",
            "cleared_items": result.get("cleared_items", 0),
            "queue_name": result.get("queue_name", "nvd_queue")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear queue: {str(e)}")


@router.post("/queue/add")
async def add_to_queue(request: Dict[str, Any]):
    """Add keyword to analysis queue"""
    try:
        keyword = request.get("keyword")
        if not keyword:
            raise HTTPException(status_code=400, detail="Keyword is required")
        job_id = queue_service.add_job(keyword, request.get("metadata", {}))
        status = "queued"
        return {
            "message": f"Keyword '{keyword}' added to analysis queue",
            "job_id": job_id,
            "keyword": keyword,
            "status": status
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add to queue: {str(e)}")


@router.post("/add_to_queue")
async def add_to_queue_alt(request: Dict[str, Any]):
    """Alternative endpoint for adding keyword to queue (frontend compatibility)"""
    return await add_to_queue(request)


@router.post("/analyze_software_async")
async def analyze_software_async(request: Dict[str, Any]):
    """Analyze multiple software packages asynchronously"""
    try:
        software_list = request.get("software_list", [])
        if not software_list:
            raise HTTPException(status_code=400, detail="Software list is required")
        job_ids = []
        jobs = []
        for software in software_list:
            job_id = queue_service.add_job(software, request.get("metadata", {}))
            job_ids.append(job_id)
            jobs.append({
                "software": software,
                "jobId": job_id,
                "keyword": software,
                "status": "queued"
            })
        return {
            "message": f"{len(jobs)} software queued for analysis",
            "job_ids": job_ids,
            "estimated_time": len(jobs) * 3,
            "jobs": jobs
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start async analysis: {str(e)}")


@router.post("/analyze_risk")
async def analyze_nvd_risk():
    """Analyze NVD risk (placeholder endpoint)"""
    try:
        # Aquí se puede implementar lógica real de análisis de riesgo
        return {
            "risk_score": 7.5,
            "risk_level": "High",
            "recommendations": [
                "Update affected software components",
                "Implement additional monitoring",
                "Review access controls"
            ],
            "vulnerability_count": 0,
            "critical_count": 0,
            "high_count": 0,
            "medium_count": 0,
            "low_count": 0
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Risk analysis failed: {str(e)}")


@router.get("/results/all")
async def get_all_job_results():
    """Get all completed job results from the queue"""
    try:
        all_results = queue_service.get_all_job_results()
        formatted_results = []
        for job in all_results.get("jobs", []):
            if job.get("status") == "completed":
                formatted_job = {
                    "job_id": job.get("job_id"),
                    "keyword": job.get("keyword"),
                    "status": job.get("status"),
                    "total_results": job.get("total_results", 0),
                    "vulnerabilities": job.get("vulnerabilities", [])[:10],
                    "processed_at": job.get("timestamp"),
                    "processed_via": job.get("processed_via", "unknown")
                }
                formatted_results.append(formatted_job)
        return {
            "success": True,
            "total_completed_jobs": len(formatted_results),
            "jobs": formatted_results,
            "message": f"Found {len(formatted_results)} completed jobs"
        }
    except Exception as e:
        return {
            "success": False,
            "total_completed_jobs": 0,
            "jobs": [],
            "error": str(e),
            "message": "Failed to retrieve job results"
        }


@router.get("/results/{job_id}")
async def get_job_results(job_id: str):
    """Get results for a specific job ID"""
    try:
        result = queue_service.get_job_result(job_id)
        if result and result.get("status") == "completed":
            return {
                "job_id": job_id,
                "status": "completed",
                "keyword": result.get("keyword"),
                "total_results": result.get("total_results", 0),
                "vulnerabilities": result.get("vulnerabilities", [])[:10],
                "processed_via": result.get("processed_via", "queue_consumer")
            }
        elif result and result.get("status") == "processing":
            return {
                "job_id": job_id,
                "status": "processing",
                "keyword": result.get("keyword"),
                "message": "Job is being processed by consumer"
            }
        elif result and result.get("status") == "failed":
            return {
                "job_id": job_id,
                "status": "failed",
                "error": result.get("error"),
                "keyword": result.get("keyword")
            }
        else:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "Job not found",
                    "job_id": job_id,
                    "message": "Job may not exist or has expired."
                }
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get job results: {str(e)}")


@router.get("/results/{job_id}/detailed")
async def get_detailed_job_results(job_id: str):
    """Get detailed results for a specific job ID with all vulnerabilities"""
    try:
        result = queue_service.get_job_result(job_id)
        if result and result.get("status") == "completed":
            return {
                "job_id": job_id,
                "status": "completed",
                "keyword": result.get("keyword"),
                "total_results": result.get("total_results", 0),
                "vulnerabilities": result.get("vulnerabilities", []),
                "processed_via": result.get("processed_via", "queue_consumer"),
                "processed_at": result.get("timestamp"),
                "risk_analysis": {
                    "high_severity": len([v for v in result.get("vulnerabilities", []) if v.get("cve", {}).get("metrics", {}).get("cvssMetricV2", [{}])[0].get("baseSeverity") == "HIGH"]),
                    "medium_severity": len([v for v in result.get("vulnerabilities", []) if v.get("cve", {}).get("metrics", {}).get("cvssMetricV2", [{}])[0].get("baseSeverity") == "MEDIUM"]),
                    "low_severity": len([v for v in result.get("vulnerabilities", []) if v.get("cve", {}).get("metrics", {}).get("cvssMetricV2", [{}])[0].get("baseSeverity") == "LOW"])
                }
            }
        elif result and result.get("status") == "processing":
            return {
                "job_id": job_id,
                "status": "processing",
                "keyword": result.get("keyword"),
                "message": "Job is being processed by consumer"
            }
        elif result and result.get("status") == "failed":
            return {
                "job_id": job_id,
                "status": "failed",
                "error": result.get("error"),
                "keyword": result.get("keyword")
            }
        else:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "Job not found",
                    "job_id": job_id,
                    "message": "Job may not exist or has expired."
                }
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get detailed job results: {str(e)}")


@router.post("/consumer/start")
async def start_consumer():
    """Start the simulated consumer to process jobs from the queue."""
    try:
        result = queue_service.start_consumer()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start consumer: {str(e)}")


@router.post("/consumer/stop")
async def stop_consumer():
    """Stop the simulated consumer."""
    try:
        result = queue_service.stop_consumer()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop consumer: {str(e)}")


@router.get("/results/mongodb")
async def get_nvd_results_from_mongodb():
    """Get all results saved in MongoDB cveScanner.jobs"""
    try:
        from app.services.mongodb_service import MongoDBService
        
        mongodb_service = MongoDBService()
        results = await mongodb_service.get_all_jobs()
        
        return {
            "success": True,
            "total_jobs": len(results),
            "source": "mongodb_cveScanner_jobs",
            "jobs": results
        }
        
    except Exception as e:
        logger.error("Error querying MongoDB: %s", str(e))
        return {
            "success": False,
            "error": str(e),
            "total_jobs": 0,
            "jobs": []
        }


@router.post("/analyze_software_async")
async def analyze_software_async(request: dict):
    """Analyze software asynchronously and queue for processing"""
    try:
        # Submit to queue for processing
        job_request = QueueJobRequest(
            keyword=request.get("keyword", ""),
            software_list=request.get("software_list", []),
            analysis_type="software_vulnerability_scan"
        )
        
        job_response = queue_service.submit_job(job_request)
        
        return {
            "success": True,
            "job_id": job_response.job_id,
            "status": "queued",
            "message": "Software analysis queued for processing"
        }
        
    except Exception as e:
        logger.error("Error in analyze_software_async: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/consumer/start")
async def start_consumer():
    """Start the NVD queue consumer"""
    try:
        result = queue_service.start_consumer()
        return {
            "success": True,
            "message": "Consumer started successfully",
            "status": result
        }
    except Exception as e:
        logger.error("Error starting consumer: %s", str(e))
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to start consumer"
        }


@router.post("/consumer/stop")
async def stop_consumer():
    """Stop the NVD queue consumer"""
    try:
        result = queue_service.stop_consumer()
        return {
            "success": True,
            "message": "Consumer stopped successfully",
            "status": result
        }
    except Exception as e:
        logger.error("Error stopping consumer: %s", str(e))
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to stop consumer"
        }


@router.get("/reports/general/keywords")
async def get_general_reports_by_keywords():
    """Get all vulnerability data grouped by keywords from MongoDB for General Reports"""
    try:
        from app.services.mongodb_service import MongoDBService
        
        mongodb_service = MongoDBService()
        keywords_data = await mongodb_service.get_reports_by_keywords()
        
        return {
            "success": True,
            "total_keywords": len(keywords_data),
            "keywords": keywords_data
        }
        
    except Exception as e:
        logger.error("Error getting general reports by keywords: %s", str(e))
        return {
            "success": False,
            "error": str(e),
            "total_keywords": 0,
            "keywords": []
        }


@router.get("/reports/general/keyword/{keyword}")
async def get_detailed_report_by_keyword(keyword: str):
    """Get detailed vulnerability report for a specific keyword from MongoDB"""
    try:
        from app.services.mongodb_service import MongoDBService
        
        mongodb_service = MongoDBService()
        report_data = await mongodb_service.get_detailed_report_by_keyword(keyword)
        
        return report_data
        
    except Exception as e:
        logger.error("Error getting detailed report for keyword %s: %s", keyword, str(e))
        return {
            "success": False,
            "error": str(e),
            "keyword": keyword,
            "jobs": [],
            "vulnerabilities": []
        }


async def process_background_job(job_id: str, request: QueueJobRequest):
    """Process a background job"""
    try:
        # Update job status to processing
        queue_service.update_job_status(job_id, "processing", progress=0.0)
        
        result = None
        
        if request.job_type == "vulnerability_search":
            # Process vulnerability search
            search_params = VulnerabilitySearchRequest(**request.parameters)
            result = await nvd_service.search_vulnerabilities(**search_params.dict())
            
        elif request.job_type == "risk_analysis":
            # Process risk analysis
            analysis_params = RiskAnalysisRequest(**request.parameters)
            
            # Get vulnerability data
            vulnerabilities_data = []
            for i, cve_id in enumerate(analysis_params.vulnerabilities):
                vuln_data = await nvd_service.get_vulnerability(cve_id)
                if vuln_data:
                    vulnerabilities_data.append(vuln_data)
                
                # Update progress
                progress = (i + 1) / len(analysis_params.vulnerabilities) * 0.8
                queue_service.update_job_status(job_id, "processing", progress=progress)
            
            # Perform analysis
            result = risk_service.analyze_risk(
                vulnerabilities_data,
                asset_criticality=analysis_params.asset_criticality,
                threat_landscape=analysis_params.threat_landscape
            )
            
        else:
            raise ValueError(f"Unknown job type: {request.job_type}")
        
        # Mark job as completed
        queue_service.complete_job(job_id, result)
        
        # If callback URL provided, send results
        if request.callback_url:
            # In a real implementation, you'd make an HTTP request to the callback URL
            pass
            
    except Exception as e:
        # Mark job as failed
        queue_service.fail_job(job_id, str(e))
