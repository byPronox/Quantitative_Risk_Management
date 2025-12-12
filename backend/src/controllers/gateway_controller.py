"""
Gateway Controller - Central proxy for all microservices
"""
import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Request
import httpx
import os

logger = logging.getLogger(__name__)
router = APIRouter()
NVD_SERVICE_URL = os.getenv("NVD_SERVICE_URL", "http://nvd-service:8002")


# =============================================================================
# HEALTH AND STATUS ENDPOINTS
# =============================================================================

@router.get("/health")
async def health_check():
    """Health check endpoint for API Gateway"""
    return {
        "status": "healthy",
        "service": "Risk Management API Gateway",
        "version": "1.0.0"
    }


@router.get("/services/status")
async def services_status():
    """Check status of all microservices"""
    services_to_check = {
        "ml_prediction": os.getenv("ML_SERVICE_URL", "http://ml-prediction-service:8001"),
        "nvd_service": os.getenv("NVD_SERVICE_URL", "http://nvd-service:8002")
    }
    
    status = {}
    
    for service_name, url in services_to_check.items():
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{url}/api/v1/health")
                if response.status_code == 200:
                    status[service_name] = "healthy"
                else:
                    status[service_name] = "unhealthy"
        except Exception as e:
            status[service_name] = f"error: {str(e)}"
    
    return {
        "gateway_status": "healthy",
        "microservices": status
    }


# =============================================================================
# NVD MICROSERVICE PROXY ENDPOINTS
# =============================================================================

@router.get("/nvd/results/all")
async def proxy_nvd_results_all():
    """Proxy to NVD microservice for retrieving all results from Database"""
    try:
        # This is the crucial change: point to the database endpoint instead of the in-memory one.
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{NVD_SERVICE_URL}/api/v1/database/results/all")
            return response.json()
    except Exception as e:
        logger.error("Error proxying to NVD service (database/results/all): %s", str(e))
        raise HTTPException(status_code=503, detail="NVD service unavailable") from e


@router.get("/nvd/queue/status")
async def proxy_nvd_queue_status():
    """Proxy to NVD microservice for queue status"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{NVD_SERVICE_URL}/api/v1/queue/status")
            return response.json()
    except Exception as e:
        logger.error("Error proxying to NVD service (queue/status): %s", str(e))
        raise HTTPException(status_code=503, detail="NVD service unavailable") from e


@router.get("/nvd/results/database")
async def proxy_nvd_results_database():
    """Proxy to NVD microservice for Database results"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{NVD_SERVICE_URL}/api/v1/database/results/all")
            return response.json()
    except Exception as e:
        logger.error("Error proxying to NVD service (results/database): %s", str(e))
        raise HTTPException(status_code=503, detail="NVD service unavailable") from e


@router.get("/nvd/results/{job_id}")
async def proxy_nvd_job_result(job_id: str):
    """Proxy to NVD microservice for a specific job result"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{NVD_SERVICE_URL}/api/v1/queue/job/{job_id}")
            return response.json()
    except Exception as e:
        logger.error("Error proxying to NVD service (results/%s): %s", job_id, str(e))
        raise HTTPException(status_code=503, detail="NVD service unavailable") from e


@router.post("/nvd/analyze_software_async")
async def proxy_nvd_analyze_software_async(request: Request):
    """Proxy to NVD microservice for asynchronous software analysis"""
    try:
        body = await request.json()
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(f"{NVD_SERVICE_URL}/api/v1/analyze_software_async", json=body)
            return response.json()
    except Exception as e:
        logger.error("Error proxying to NVD service (analyze_software_async): %s", str(e))
        raise HTTPException(status_code=503, detail="NVD service unavailable") from e


@router.post("/nvd/queue/consumer/start")
async def proxy_nvd_consumer_start():
    """Proxy to NVD microservice to start the consumer"""
    try:
        async with httpx.AsyncClient(timeout=60.0) as client: # Increased timeout as this can be a long operation
            response = await client.post(f"{NVD_SERVICE_URL}/api/v1/queue/consumer/start")
            return response.json()
    except Exception as e:
        logger.error("Error proxying to NVD service (consumer/start): %s", str(e))
        raise HTTPException(status_code=503, detail="NVD service unavailable") from e


@router.post("/nvd/queue/consumer/stop")
async def proxy_nvd_consumer_stop():
    """Proxy to NVD microservice to stop the consumer"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(f"{NVD_SERVICE_URL}/api/v1/queue/consumer/stop")
            return response.json()
    except Exception as e:
        logger.error("Error proxying to NVD service (consumer/stop): %s", str(e))
        raise HTTPException(status_code=503, detail="NVD service unavailable") from e


@router.post("/nvd/queue/bulk-save")
async def proxy_nvd_bulk_save():
    """Proxy to NVD microservice to bulk save all completed jobs to Database"""
    try:
        async with httpx.AsyncClient(timeout=60.0) as client: # Increased timeout
            response = await client.post(f"{NVD_SERVICE_URL}/api/v1/database/bulk-save")
            return response.json()
    except Exception as e:
        logger.error("Error proxying to NVD service (bulk-save): %s", str(e))
        raise HTTPException(status_code=503, detail="NVD service unavailable") from e


# =============================================================================
# REPORT MICROSERVICE PROXY ENDPOINTS  
# =============================================================================

@router.get("/reports/general/keywords")
async def proxy_reports_general_keywords():
    """Proxy to NVD microservice for Database reports by keywords"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{NVD_SERVICE_URL}/api/v1/database/reports/keywords")
            return response.json()
    except Exception as e:
        logger.error("Error proxying to NVD service (database/reports/keywords): %s", str(e))
        raise HTTPException(status_code=503, detail="NVD service unavailable") from e


@router.get("/reports/general/keyword/{keyword}")
async def proxy_reports_detailed_keyword(keyword: str):
    """Proxy to NVD microservice for detailed Database keyword report"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{NVD_SERVICE_URL}/api/v1/database/reports/detailed/{keyword}")
            return response.json()
    except Exception as e:
        logger.error("Error proxying to NVD service (database/reports/detailed/%s): %s", keyword, str(e))
        raise HTTPException(status_code=503, detail="NVD service unavailable") from e


# =============================================================================
# LEGACY KONG GATEWAY ENDPOINTS (for backward compatibility)
# =============================================================================

@router.get("/nvd")
async def proxy_nvd_kong(keyword: str = ""):
    """Proxy to Kong Gateway for vulnerability search (legacy compatibility)"""
    try:
        kong_url = os.getenv("KONG_PROXY_URL")
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{kong_url}/nvd/v2/cves",
                params={"keywordSearch": keyword.strip() if keyword.strip() else "vulnerability", "resultsPerPage": 20}
            )
            if response.status_code != 200:
                logger.error("Kong NVD service error: %s - %s", response.status_code, response.text)
                raise HTTPException(status_code=response.status_code, detail="NVD search via Kong failed")
            return response.json()
    except Exception as e:
        logger.error("Error proxying to Kong NVD service: %s", str(e))
        raise HTTPException(status_code=503, detail="NVD service unavailable") from e


# =============================================================================
# GENERIC PROXY ENDPOINT
# =============================================================================

@router.get("/proxy/{service_name}/{path:path}")
async def proxy_to_microservice(service_name: str, path: str):
    """Generic GET proxy requests to microservices"""
    services = {
        "ml": os.getenv("ML_SERVICE_URL", "http://ml-prediction-service:8001"),
        "nvd": os.getenv("NVD_SERVICE_URL", "http://nvd-service:8002")
    }
    
    if service_name not in services:
        raise HTTPException(status_code=404, detail=f"Service {service_name} not found")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{services[service_name]}/api/v1/{path}")
            return response.json()
    except Exception as e:
        logger.error("Error proxying to %s: %s", service_name, str(e))
        raise HTTPException(status_code=503, detail=f"Service {service_name} unavailable") from e


@router.get("/nvd/database/reports/keywords")
async def proxy_nvd_database_reports_keywords():
    """Proxy to NVD microservice for Database reports grouped by keywords"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{NVD_SERVICE_URL}/api/v1/database/reports/keywords")
            return response.json()
    except Exception as e:
        logger.error("Error proxying to NVD service (database/reports/keywords): %s", str(e))
        raise HTTPException(status_code=503, detail="NVD service unavailable") from e


@router.get("/nvd/database/reports/detailed/{keyword}")
async def proxy_nvd_database_detailed_report(keyword: str):
    """Proxy to NVD microservice for detailed Database report by keyword"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{NVD_SERVICE_URL}/api/v1/database/reports/detailed/{keyword}")
            return response.json()
    except Exception as e:
        logger.error("Error proxying to NVD service (database/reports/detailed/%s): %s", keyword, str(e))
        raise HTTPException(status_code=503, detail="NVD service unavailable") from e


@router.get("/nvd/database/health")
async def proxy_nvd_database_health():
    """Proxy to NVD microservice for Database health check"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{NVD_SERVICE_URL}/api/v1/database/health")
            return response.json()
    except Exception as e:
        logger.error("Error proxying to NVD service (database/health): %s", str(e))
        raise HTTPException(status_code=503, detail="NVD service unavailable") from e


@router.post("/nvd/database/analyze")
async def proxy_nvd_database_analyze(request: Request):
    """Proxy to NVD microservice for analyzing CVEs and saving to Database"""
    try:
        body = await request.json()
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(f"{NVD_SERVICE_URL}/api/v1/database/analyze", json=body)
            return response.json()
    except Exception as e:
        logger.error("Error proxying to NVD service (database/analyze): %s", str(e))
        raise HTTPException(status_code=503, detail="NVD service unavailable") from e
