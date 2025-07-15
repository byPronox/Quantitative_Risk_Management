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
        # This would normally call a service to get reports from database
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
