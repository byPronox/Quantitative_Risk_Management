"""
ML Prediction controller - Legacy compatibility for microservices
Maintains compatibility with existing frontend while redirecting to ML microservice
"""
import logging
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import httpx

from config.settings import settings

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/predict/combined/")
async def predict_combined_legacy(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Legacy endpoint for combined prediction - redirects to ML microservice
    This maintains compatibility with the existing frontend
    
    The frontend expects this endpoint to exist, so we proxy the request
    to the ML microservice at: ML_SERVICE_URL/predict/combined/
    """
    try:
        logger.info(f"Proxying prediction request to ML microservice: {settings.ML_SERVICE_URL}")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{settings.ML_SERVICE_URL}/predict/combined/",
                json=request,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "Risk-Management-Gateway/1.0"
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info("ML microservice responded successfully")
                return result
            else:
                logger.error(f"ML service returned status {response.status_code}: {response.text}")
                raise HTTPException(
                    status_code=response.status_code, 
                    detail=f"ML service error: {response.text}"
                )
                
    except httpx.ConnectError as e:
        logger.error(f"Failed to connect to ML service at {settings.ML_SERVICE_URL}: {e}")
        raise HTTPException(
            status_code=503, 
            detail=f"ML prediction service unavailable at {settings.ML_SERVICE_URL}"
        )
    except httpx.TimeoutException as e:
        logger.error(f"ML service timeout: {e}")
        raise HTTPException(
            status_code=504, 
            detail="ML prediction service timeout"
        )
    except httpx.RequestError as e:
        logger.error(f"Request error to ML service: {e}")
        raise HTTPException(
            status_code=503, 
            detail="ML prediction service request failed"
        )
    except Exception as e:
        logger.error(f"Unexpected error in predict_combined: {e}")
        raise HTTPException(
            status_code=500, 
            detail="Internal server error in prediction gateway"
        )


@router.options("/predict/combined/")
async def predict_combined_options():
    """
    CORS preflight for /predict/combined/ endpoint
    Required for frontend CORS requests
    """
    return {
        "message": "CORS preflight OK",
        "methods": ["POST", "OPTIONS"],
        "service": "ML Prediction Gateway"
    }


@router.get("/predict/health")
async def predict_health() -> Dict[str, Any]:
    """
    Health check endpoint for ML prediction service
    This checks if the ML microservice is responding
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{settings.ML_SERVICE_URL}/health")
            
            if response.status_code == 200:
                ml_status = response.json()
                return {
                    "status": "healthy",
                    "ml_service": "available",
                    "ml_service_url": settings.ML_SERVICE_URL,
                    "ml_service_response": ml_status,
                    "gateway": "ok"
                }
            else:
                return {
                    "status": "degraded",
                    "ml_service": "unavailable", 
                    "ml_service_url": settings.ML_SERVICE_URL,
                    "ml_service_status": response.status_code,
                    "gateway": "ok"
                }
                
    except Exception as e:
        logger.error(f"ML service health check failed: {e}")
        return {
            "status": "unhealthy",
            "ml_service": "unavailable",
            "ml_service_url": settings.ML_SERVICE_URL,
            "error": str(e),
            "gateway": "ok"
        }


@router.get("/predict/status")
async def predict_status() -> Dict[str, Any]:
    """
    Detailed status of ML prediction capabilities
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Try to get detailed status from ML service
            try:
                response = await client.get(f"{settings.ML_SERVICE_URL}/status")
                if response.status_code == 200:
                    ml_detailed_status = response.json()
                else:
                    ml_detailed_status = {"error": f"Status endpoint returned {response.status_code}"}
            except:
                ml_detailed_status = {"error": "Status endpoint not available"}
            
            # Basic health check
            health_response = await client.get(f"{settings.ML_SERVICE_URL}/health")
            ml_available = health_response.status_code == 200
            
            return {
                "prediction_service": {
                    "available": ml_available,
                    "url": settings.ML_SERVICE_URL,
                    "endpoints": {
                        "/predict/combined/": "Combined ML prediction",
                        "/predict/health": "Health check", 
                        "/predict/status": "Detailed status"
                    },
                    "detailed_status": ml_detailed_status
                },
                "gateway_info": {
                    "version": settings.API_VERSION,
                    "compatibility_mode": "legacy_frontend"
                }
            }
            
    except Exception as e:
        logger.error(f"Failed to get ML service status: {e}")
        return {
            "prediction_service": {
                "available": False,
                "url": settings.ML_SERVICE_URL,
                "error": str(e)
            },
            "gateway_info": {
                "version": settings.API_VERSION,
                "compatibility_mode": "legacy_frontend"
            }
        }
