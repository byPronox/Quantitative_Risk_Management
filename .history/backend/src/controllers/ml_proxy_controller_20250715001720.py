"""
ML Proxy Controller - Routes requests to ML microservice
"""
import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Request

from ..services.ml_service import MLService, MLServiceError, MLServiceUnavailableError, MLServiceRequestError

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize ML service
ml_service = MLService()


@router.post("/predict/combined/")
async def predict_combined(request: Request) -> Dict[str, Any]:
    """
    Proxy endpoint for combined ML predictions
    Forwards request to ML microservice
    """
    try:
        # Get request body as JSON
        request_data = await request.json()
        
        logger.info("Proxying combined prediction request to ML microservice")
        
        # Forward to ML microservice
        result = await ml_service.predict_combined(request_data)
        
        logger.info("Successfully received response from ML microservice")
        return result
        
    except MLServiceUnavailableError as e:
        logger.error("ML microservice unavailable: %s", str(e))
        raise HTTPException(
            status_code=503,
            detail="ML prediction service is currently unavailable"
        )
    except MLServiceRequestError as e:
        logger.error("ML microservice request error: %s", str(e))
        raise HTTPException(
            status_code=502,
            detail="Error communicating with ML prediction service"
        )
    except MLServiceError as e:
        logger.error("ML service error: %s", str(e))
        raise HTTPException(
            status_code=500,
            detail="Internal error in ML prediction service"
        )
    except Exception as e:
        logger.error("Unexpected error in ML proxy: %s", str(e))
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred"
        )


@router.get("/predict/health")
async def predict_health() -> Dict[str, Any]:
    """
    Health check for ML microservice
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{settings.ML_SERVICE_URL}/health")
            
            if response.status_code == 200:
                return {
                    "status": "healthy",
                    "ml_service": response.json(),
                    "proxy": "backend gateway"
                }
            else:
                return {
                    "status": "unhealthy", 
                    "ml_service_status": response.status_code,
                    "proxy": "backend gateway"
                }
                
    except Exception as e:
        logger.error(f"ML microservice health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "proxy": "backend gateway"
        }


@router.post("/predict/")
async def predict_single(request: Request) -> Dict[str, Any]:
    """
    Proxy endpoint for single ML prediction - forwards to ML microservice
    """
    try:
        # Get the request body
        body = await request.body()
        
        # Forward the request to ML microservice
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{settings.ML_SERVICE_URL}/predict/",
                content=body,
                headers={
                    "Content-Type": "application/json",
                    **dict(request.headers)
                }
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"ML microservice error: {response.status_code} - {response.text}")
                raise HTTPException(
                    status_code=response.status_code, 
                    detail=f"ML microservice error: {response.text}"
                )
                
    except httpx.RequestError as e:
        logger.error(f"Failed to connect to ML microservice: {e}")
        raise HTTPException(
            status_code=503, 
            detail="ML microservice unavailable"
        )
    except Exception as e:
        logger.error(f"ML prediction proxy failed: {e}")
        raise HTTPException(
            status_code=500, 
            detail="ML prediction failed"
        )
