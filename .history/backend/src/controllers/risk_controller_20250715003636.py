"""
Risk analysis controller
"""
import logging
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List
import httpx

from config.settings import settings
from services.risk_service import RiskService
from models.risk_models import RiskAnalysisRequest, RiskAnalysisResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/risk/analyze")
async def analyze_risk(
    request: RiskAnalysisRequest,
    risk_service: RiskService = Depends()
) -> RiskAnalysisResponse:
    """
    Analyze risk for given assets or software components
    """
    try:
        result = await risk_service.analyze_risk(request)
        return result
    except Exception as e:
        logger.error(f"Risk analysis failed: {e}")
        raise HTTPException(status_code=500, detail="Risk analysis failed")


@router.get("/risk/reports")
async def get_risk_reports() -> List[Dict[str, Any]]:
    """
    Get all risk analysis reports
    """
    try:
        # This calls the report microservice
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{settings.REPORT_SERVICE_URL}/api/v1/reports")
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(status_code=response.status_code, detail="Failed to fetch reports")
    except httpx.RequestError as e:
        logger.error(f"Failed to fetch reports: {e}")
        raise HTTPException(status_code=503, detail="Report service unavailable")


@router.get("/risk/matrix")
async def get_risk_matrix() -> Dict[str, Any]:
    """
    Get risk matrix data for visualization
    """
    try:
        risk_service = RiskService()
        matrix_data = await risk_service.get_risk_matrix()
        return matrix_data
    except Exception as e:
        logger.error(f"Failed to get risk matrix: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate risk matrix")


# =============================================================================
# COMPATIBILITY ENDPOINTS - Redirect to ML Microservice
# =============================================================================

@router.post("/predict/combined/")
async def predict_combined_legacy(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Legacy endpoint for combined prediction - redirects to ML microservice
    This maintains compatibility with the existing frontend
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{settings.ML_SERVICE_URL}/api/v1/predict/combined",
                json=request,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"ML service returned status {response.status_code}")
                raise HTTPException(
                    status_code=response.status_code, 
                    detail=f"ML service error: {response.text}"
                )
                
    except httpx.RequestError as e:
        logger.error(f"Failed to connect to ML service: {e}")
        raise HTTPException(
            status_code=503, 
            detail="ML prediction service unavailable"
        )
    except Exception as e:
        logger.error(f"Unexpected error in predict_combined: {e}")
        raise HTTPException(
            status_code=500, 
            detail="Internal server error"
        )


@router.options("/predict/combined/")
async def predict_combined_options():
    """
    CORS preflight for /predict/combined/ endpoint
    """
    return {"message": "OK"}


@router.get("/predict/health")
async def predict_health() -> Dict[str, Any]:
    """
    Health check endpoint for ML prediction service
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{settings.ML_SERVICE_URL}/api/v1/health")
            
            if response.status_code == 200:
                ml_status = response.json()
                return {
                    "ml_service": "available",
                    "ml_service_response": ml_status,
                    "gateway": "ok"
                }
            else:
                return {
                    "ml_service": "unavailable",
                    "ml_service_status": response.status_code,
                    "gateway": "ok"
                }
                
    except Exception as e:
        logger.error(f"ML service health check failed: {e}")
        return {
            "ml_service": "unavailable",
            "error": str(e),
            "gateway": "ok"
        }
