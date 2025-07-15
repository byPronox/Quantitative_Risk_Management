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
    services = {
        "ml_prediction": os.getenv("ML_SERVICE_URL", "http://ml-prediction-service:8001"),
        "nvd_service": os.getenv("NVD_SERVICE_URL", "http://nvd-service:8002"),
        "report_service": os.getenv("REPORT_SERVICE_URL", "http://report-service:8003")
    }
    
    status = {}
    
    for service_name, url in services.items():
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
    """Proxy to NVD microservice for retrieving all results from MongoDB"""
    try:
        nvd_service_url = os.getenv("NVD_SERVICE_URL", "http://nvd-service:8002")
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{nvd_service_url}/api/v1/mongodb/results/all")
            return response.json()
    except Exception as e:
        logger.error("Error proxying to NVD service (mongodb/results/all): %s", str(e))
        raise HTTPException(status_code=503, detail="NVD service unavailable") from e


@router.get("/nvd/queue/status")
async def proxy_nvd_queue_status():
    """Proxy to NVD microservice for queue status"""
    try:
        nvd_service_url = os.getenv("NVD_SERVICE_URL", "http://nvd-service:8002")
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{nvd_service_url}/api/v1/queue/status")
            return response.json()
    except Exception as e:
        logger.error("Error proxying to NVD service (queue/status): %s", str(e))
        raise HTTPException(status_code=503, detail="NVD service unavailable") from e


@router.get("/nvd/results/mongodb")
async def proxy_nvd_results_mongodb():
    """Proxy to NVD microservice for MongoDB results"""
    try:
        nvd_service_url = os.getenv("NVD_SERVICE_URL", "http://nvd-service:8002")
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{nvd_service_url}/api/v1/results/mongodb")
            return response.json()
    except Exception as e:
        logger.error("Error proxying to NVD service (results/mongodb): %s", str(e))
        raise HTTPException(status_code=503, detail="NVD service unavailable") from e


@router.get("/nvd/results/{job_id}")
async def proxy_nvd_job_result(job_id: str):
    """Proxy to NVD microservice for a specific job result"""
    try:
        nvd_service_url = os.getenv("NVD_SERVICE_URL", "http://nvd-service:8002")
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{nvd_service_url}/api/v1/results/{job_id}")
            return response.json()
    except Exception as e:
        logger.error("Error proxying to NVD service (results/%s): %s", job_id, str(e))
        raise HTTPException(status_code=503, detail="NVD service unavailable") from e


@router.post("/nvd/analyze_software_async")
async def proxy_nvd_analyze_software_async(request: Request):
    """Proxy to NVD microservice for asynchronous software analysis"""
    try:
        body = await request.json()
        nvd_service_url = os.getenv("NVD_SERVICE_URL", "http://nvd-service:8002")
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(f"{nvd_service_url}/api/v1/analyze_software_async", json=body)
            return response.json()
    except Exception as e:
        logger.error("Error proxying to NVD service (analyze_software_async): %s", str(e))
        raise HTTPException(status_code=503, detail="NVD service unavailable") from e


@router.post("/nvd/consumer/start")
async def proxy_nvd_consumer_start():
    """Proxy to NVD microservice to start the consumer"""
    try:
        nvd_service_url = os.getenv("NVD_SERVICE_URL", "http://nvd-service:8002")
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(f"{nvd_service_url}/api/v1/consumer/start")
            return response.json()
    except Exception as e:
        logger.error("Error proxying to NVD service (consumer/start): %s", str(e))
        raise HTTPException(status_code=503, detail="NVD service unavailable") from e


@router.post("/nvd/consumer/stop")
async def proxy_nvd_consumer_stop():
    """Proxy to NVD microservice to stop the consumer"""
    try:
        nvd_service_url = os.getenv("NVD_SERVICE_URL", "http://nvd-service:8002")
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(f"{nvd_service_url}/api/v1/consumer/stop")
            return response.json()
    except Exception as e:
        logger.error("Error proxying to NVD service (consumer/stop): %s", str(e))
        raise HTTPException(status_code=503, detail="NVD service unavailable") from e


@router.post("/nvd/queue/consumer/start")
async def proxy_nvd_queue_consumer_start():
    """Alias for starting NVD queue consumer (frontend compatibility)"""
    return await proxy_nvd_consumer_start()


@router.post("/nvd/queue/consumer/stop") 
async def proxy_nvd_queue_consumer_stop():
    """Alias for stopping NVD queue consumer (frontend compatibility)"""
    return await proxy_nvd_consumer_stop()


# =============================================================================
# REPORT MICROSERVICE PROXY ENDPOINTS  
# =============================================================================

@router.get("/reports/general/keywords")
async def proxy_reports_general_keywords():
    """Proxy to Report microservice for general reports by keywords"""
    try:
        nvd_service_url = os.getenv("NVD_SERVICE_URL", "http://nvd-service:8002")
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{nvd_service_url}/api/v1/reports/general/keywords")
            return response.json()
    except Exception as e:
        logger.error("Error proxying to NVD service (reports/general/keywords): %s", str(e))
        raise HTTPException(status_code=503, detail="Report service unavailable") from e


@router.get("/reports/general/keyword/{keyword}")
async def proxy_reports_detailed_keyword(keyword: str):
    """Proxy to Report microservice for detailed keyword report"""
    try:
        nvd_service_url = os.getenv("NVD_SERVICE_URL", "http://nvd-service:8002")
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{nvd_service_url}/api/v1/reports/general/keyword/{keyword}")
            return response.json()
    except Exception as e:
        logger.error("Error proxying to NVD service (reports/general/keyword/%s): %s", keyword, str(e))
        raise HTTPException(status_code=503, detail="Report service unavailable") from e


# =============================================================================
# LEGACY KONG GATEWAY ENDPOINTS (for backward compatibility)
# =============================================================================

@router.get("/nvd")
async def proxy_nvd_kong(keyword: str = ""):
    """Proxy to Kong Gateway for vulnerability search (legacy compatibility)"""
    try:
        kong_url = os.getenv("KONG_URL", "https://kong-b27b67aff4usnspl9.kongcloud.dev")
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{kong_url}/nvd/cves/2.0",
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
    """Generic proxy requests to microservices"""
    services = {
        "ml": os.getenv("ML_SERVICE_URL", "http://ml-prediction-service:8001"),
        "nvd": os.getenv("NVD_SERVICE_URL", "http://nvd-service:8002"),
        "report": os.getenv("REPORT_SERVICE_URL", "http://report-service:8003")
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
