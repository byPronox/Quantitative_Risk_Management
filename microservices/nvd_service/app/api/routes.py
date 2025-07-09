from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from typing import Optional, Dict, Any
import uuid
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


@router.get("/queue/status")
async def get_queue_status():
    """Get overall queue status"""
    try:
        status = queue_service.get_queue_status()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get queue status: {str(e)}")


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
