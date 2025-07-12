from fastapi import APIRouter, HTTPException, Request
from typing import Dict, Any
import httpx
import os
import logging
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