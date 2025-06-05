# backend/app/api/nvd.py
from fastapi import APIRouter
import httpx
import os

router = APIRouter()

NVD_API_KEY = os.getenv("NVD_API_KEY")
NVD_API_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"

@router.get("/nvd")
async def get_vulnerabilities(keyword: str = "react"):
    headers = {
        "apiKey": NVD_API_KEY
    }
    params = {
        "keywordSearch": keyword,
        "startIndex": 0,
        "resultsPerPage": 10
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(NVD_API_URL, headers=headers, params=params)
        return response.json()
