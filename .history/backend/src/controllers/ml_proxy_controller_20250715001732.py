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
async def ml_health_check() -> Dict[str, Any]:
    """
    Check health of ML microservice
    """
    try:
        health_status = await ml_service.health_check()
        
        # Return appropriate HTTP status based on ML service health
        if health_status.get("status") == "healthy":
            return health_status
        else:
            # Return unhealthy status but don't raise exception
            # Let client decide how to handle
            return health_status
            
    except Exception as e:
        logger.error("Error checking ML service health: %s", str(e))
        return {
            "status": "error",
            "error": "Failed to check ML service health",
            "service_url": ml_service.base_url
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
