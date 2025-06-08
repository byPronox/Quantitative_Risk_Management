# backend/app/api/nvd.py
from fastapi import APIRouter, HTTPException
import httpx
import logging
from config.config import settings

router = APIRouter()

NVD_API_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
logger = logging.getLogger(__name__)

# Use lazy logging formatting for best practices
@router.get("/nvd")
async def get_vulnerabilities(keyword: str = "react"):
    headers = {
        "apiKey": settings.NVD_API_KEY
    }
    params = {
        "keywordSearch": keyword,
        "startIndex": 0,
        "resultsPerPage": 10
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(NVD_API_URL, headers=headers, params=params)
            response.raise_for_status()
            logger.info("NVD query for keyword '%s' succeeded.", keyword)
            return response.json()
    except Exception as e:
        logger.error("NVD API request failed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch vulnerabilities from NVD API.") from e
