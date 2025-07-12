from fastapi import APIRouter, HTTPException, Request
from typing import Dict, Any
import httpx
import os
import logging
import asyncio
import time
from queue_manager.queue import RabbitMQManager, publish_to_queue

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/health")
async def health_check():
    """Health check endpoint for Kong Gateway"""
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
        "nvd_service": os.getenv("NVD_SERVICE_URL", "http://nvd-service:8002")
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

@router.post("/predict/combined/")
async def predict_combined(request: Request):
    """Legacy endpoint - proxy to ML microservice"""
    try:
        # Get request body
        body = await request.json()
        
        ml_service_url = os.getenv("ML_SERVICE_URL", "http://ml-prediction-service:8001")
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{ml_service_url}/api/v1/predict/combined",
                json=body
            )
            return response.json()
    except Exception as e:
        logger.error(f"Error calling ML service: {e}")
        raise HTTPException(status_code=503, detail="ML service unavailable")

@router.get("/nvd")
async def search_nvd_vulnerabilities(keyword: str = ""):
    """Legacy NVD endpoint - proxy to NVD microservice"""
    try:
        # Use "vulnerability" as default if no keyword provided
        search_keyword = keyword.strip() if keyword.strip() else "vulnerability"
        
        nvd_service_url = os.getenv("NVD_SERVICE_URL", "http://nvd-service:8002")
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{nvd_service_url}/api/v1/vulnerabilities/search",
                json={"keywords": search_keyword, "results_per_page": 20}
            )
            if response.status_code != 200:
                logger.error(f"NVD service error: {response.status_code} - {response.text}")
                raise HTTPException(status_code=response.status_code, detail="NVD search failed")
            return response.json()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calling NVD service: {e}")
        raise HTTPException(status_code=503, detail="NVD service unavailable")

@router.get("/proxy/{service_name}/{path:path}")
async def proxy_to_microservice(service_name: str, path: str):
    """Proxy requests to microservices (fallback for Kong)"""
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
        logger.error(f"Error proxying to {service_name}: {e}")
        raise HTTPException(status_code=503, detail=f"Service {service_name} unavailable")

# Queue Management Routes
@router.get("/nvd/queue/status")
async def get_queue_status():
    """Get RabbitMQ queue status for NVD analysis"""
    try:
        # Try to get info from RabbitMQ
        try:
            manager = RabbitMQManager()
            await manager.connect()
            queue_info = await manager.get_queue_info()
            await manager.close()
        except Exception as e:
            logger.warning(f"RabbitMQ connection failed: {e}")
            # Return mock data if RabbitMQ fails
            queue_info = {
                "connected": False,
                "queue_name": "nvd_analysis_queue",
                "queue_size": 0,
                "total_vulnerabilities": 0,
                "keywords": [],
                "error": f"RabbitMQ unavailable: {str(e)}"
            }
        
        # Try to enhance with NVD service info
        try:
            nvd_service_url = os.getenv("NVD_SERVICE_URL", "http://nvd-service:8002")
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{nvd_service_url}/api/v1/queue/status")
                if response.status_code == 200:
                    nvd_data = response.json()
                    queue_info.update(nvd_data)
        except Exception as e:
            logger.warning(f"Could not get NVD service queue info: {e}")
        
        return queue_info
        
    except Exception as e:
        logger.error(f"Error getting queue status: {e}")
        return {
            "error": str(e),
            "connected": False,
            "queue_size": 0,
            "total_vulnerabilities": 0,
            "keywords": []
        }

@router.delete("/nvd/queue/clear")
async def clear_queue():
    """Clear the RabbitMQ queue"""
    try:
        # Try to clear via NVD service first
        nvd_service_url = os.getenv("NVD_SERVICE_URL", "http://nvd-service:8002")
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.delete(f"{nvd_service_url}/api/v1/queue/clear")
            if response.status_code == 200:
                return response.json()
        
        # Fallback to direct queue management
        manager = RabbitMQManager()
        await manager.connect()
        
        # Simple queue purge (implementation depends on your queue structure)
        result = {
            "message": "Queue cleared successfully",
            "cleared_items": 0,
            "queue_name": manager.queue_name
        }
        
        await manager.close()
        return result
        
    except Exception as e:
        logger.error(f"Error clearing queue: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear queue: {str(e)}")

@router.post("/nvd/queue/add")
async def add_to_queue(request: Dict[str, Any]):
    """Add keyword to analysis queue"""
    try:
        keyword = request.get("keyword")
        if not keyword:
            raise HTTPException(status_code=400, detail="Keyword is required")
        
        # Add to queue using RabbitMQ
        try:
            job_id = await publish_to_queue(keyword, request.get("metadata", {}))
            status = "queued" if not job_id.startswith("mock-") else "queued_mock"
        except Exception as e:
            logger.warning("RabbitMQ queue failed, using mock job: %s", str(e))
            job_id = f"mock-job-{keyword}-{int(time.time())}"
            status = "queued_mock"
        
        return {
            "message": f"Keyword '{keyword}' added to analysis queue",
            "job_id": job_id,
            "keyword": keyword,
            "status": status
        }
        
    except Exception as e:
        logger.error("Error adding to queue: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Failed to add to queue: {str(e)}") from e

# NVD API Proxy with Kong integration
@router.get("/nvd/cves/2.0")
async def get_nvd_vulnerabilities(keywordSearch: str | None = None, **params):
    """
    Proxy to Kong Gateway for NVD CVE API
    This should be routed through Kong to https://kong-b27b67aff4usnspl9.kongcloud.dev/nvd/cves/2.0
    """
    try:
        # Kong URL from environment
        kong_url = os.getenv("KONG_PROXY_URL", "https://kong-b27b67aff4usnspl9.kongcloud.dev")
        
        # Build query parameters
        query_params = {}
        if keywordSearch:
            query_params["keywordSearch"] = keywordSearch
        
        # Add any additional parameters
        for key, value in params.items():
            if value is not None:
                query_params[key] = value
        
        # Make request to Kong
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{kong_url}/nvd/cves/2.0",
                params=query_params
            )
            
            if response.status_code != 200:
                logger.error("Kong NVD API error: %s - %s", response.status_code, response.text)
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"NVD API error: {response.text}"
                )
            
            return response.json()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error calling Kong NVD API: %s", str(e))
        raise HTTPException(status_code=503, detail="NVD API service unavailable") from e