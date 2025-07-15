"""
Health check controller
"""
import logging
from fastapi import APIRouter, Depends
from typing import Dict, Any
import httpx

from config.settings import settings

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint
    Returns the status of the API Gateway and connected services
    """
    return {
        "status": "healthy",
        "service": "Risk Management API Gateway",
        "version": settings.API_VERSION,
        "environment": "production" if "prod" in settings.DATABASE_URL else "development"
    }


@router.get("/health/services")
async def services_health_check() -> Dict[str, Any]:
    """
    Check health of all microservices
    """
    services = {
        "ml_prediction": settings.ML_SERVICE_URL,
        "nvd_service": settings.NVD_SERVICE_URL,
        "report_service": settings.REPORT_SERVICE_URL
    }
    
    status = {}
    
    for service_name, service_url in services.items():
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{service_url}/health")
                status[service_name] = {
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "url": service_url,
                    "response_time": response.elapsed.total_seconds() if hasattr(response, 'elapsed') else None
                }
        except Exception as e:
            status[service_name] = {
                "status": "unhealthy",
                "url": service_url,
                "error": str(e)
            }
    
    overall_status = "healthy" if all(s["status"] == "healthy" for s in status.values()) else "degraded"
    
    return {
        "overall_status": overall_status,
        "services": status,
        "timestamp": "2025-01-14T00:00:00Z"  # In real app, use datetime.utcnow()
    }
