"""
NVD (National Vulnerability Database) controller
"""
import logging
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List, Optional
import httpx

from config.settings import settings
from services.nvd_service import NVDService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/nvd/vulnerabilities")
async def get_vulnerabilities(
    cpe_name: Optional[str] = Query(None, description="CPE name to search for"),
    keyword: Optional[str] = Query(None, description="Keyword to search for"),
    limit: int = Query(10, description="Number of results to return", ge=1, le=100)
) -> Dict[str, Any]:
    """
    Get vulnerabilities from NVD
    """
    try:
        nvd_service = NVDService()
        vulnerabilities = await nvd_service.get_vulnerabilities(
            cpe_name=cpe_name,
            keyword=keyword,
            limit=limit
        )
        return vulnerabilities
    except Exception as e:
        logger.error(f"Failed to fetch NVD vulnerabilities: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch vulnerabilities")


@router.get("/nvd/cpe")
async def search_cpe(
    keyword: str = Query(..., description="Keyword to search for CPE"),
    limit: int = Query(10, description="Number of results to return", ge=1, le=100)
) -> List[Dict[str, Any]]:
    """
    Search for CPE (Common Platform Enumeration) entries
    """
    try:
        nvd_service = NVDService()
        cpe_results = await nvd_service.search_cpe(keyword=keyword, limit=limit)
        return cpe_results
    except Exception as e:
        logger.error(f"Failed to search CPE: {e}")
        raise HTTPException(status_code=500, detail="Failed to search CPE")


@router.post("/nvd/analyze")
async def analyze_software(
    software_list: List[str]
) -> Dict[str, Any]:
    """
    Analyze a list of software for vulnerabilities
    """
    try:
        nvd_service = NVDService()
        analysis_result = await nvd_service.analyze_software_list(software_list)
        return analysis_result
    except Exception as e:
        logger.error(f"Software analysis failed: {e}")
        raise HTTPException(status_code=500, detail="Software analysis failed")
