"""
NVD Unified Controller - Single source of truth for NVD operations
"""
import logging
from fastapi import APIRouter, HTTPException, Query, Body
from typing import Dict, Any, List, Optional
import httpx
import os

from config.settings import settings

logger = logging.getLogger(__name__)
router = APIRouter()

# NVD Service URL
NVD_SERVICE_URL = os.getenv("NVD_SERVICE_URL", "http://nvd-service:8002")

@router.get("/nvd/vulnerabilities")
async def get_vulnerabilities(
    keyword: Optional[str] = Query(None, description="Keyword to search for"),
    cpe_name: Optional[str] = Query(None, description="CPE name to search for"),
    limit: int = Query(10, description="Number of results to return", ge=1, le=100)
) -> Dict[str, Any]:
    """
    Get vulnerabilities from NVD API via Kong Gateway
    """
    try:
        # Use Kong Gateway for NVD API calls
        kong_url = settings.KONG_PROXY_URL
        params = {
            "resultsPerPage": min(limit, 2000),
            "startIndex": 0
        }
        
        if cpe_name:
            params["cpeName"] = cpe_name
        if keyword:
            params["keywordSearch"] = keyword
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{kong_url}/nvd/cves/2.0",
                params=params,
                headers={"apiKey": settings.NVD_API_KEY} if settings.NVD_API_KEY else {}
            )
            
            if response.status_code == 200:
                data = response.json()
                vulnerabilities = data.get("vulnerabilities", [])
                return {
                    "vulnerabilities": vulnerabilities,
                    "totalResults": data.get("totalResults", 0),
                    "success": True
                }
            else:
                logger.error(f"NVD API error: {response.status_code} - {response.text}")
                return {
                    "vulnerabilities": [],
                    "totalResults": 0,
                    "success": False,
                    "error": f"NVD API error: {response.status_code}"
                }
                
    except Exception as e:
        logger.error(f"Failed to fetch NVD vulnerabilities: {e}")
        return {
            "vulnerabilities": [],
            "totalResults": 0,
            "success": False,
            "error": str(e)
        }

@router.post("/nvd/analyze_software_async")
async def analyze_software_async(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze software asynchronously using NVD microservice
    """
    try:
        software_list = request.get("software_list", [])
        metadata = request.get("metadata", {})
        
        if not software_list:
            raise HTTPException(status_code=400, detail="Software list is required")
        
        # Call NVD microservice
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{NVD_SERVICE_URL}/api/v1/analyze_software_async",
                json={
                    "software_list": software_list,
                    "metadata": metadata
                }
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"NVD service error: {response.status_code} - {response.text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"NVD service error: {response.text}"
                )
                
    except httpx.RequestError as e:
        logger.error(f"Failed to connect to NVD service: {e}")
        raise HTTPException(status_code=503, detail="NVD service unavailable")
    except Exception as e:
        logger.error(f"Unexpected error in analyze_software_async: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/nvd/results/all")
async def get_all_results() -> Dict[str, Any]:
    """
    Get all results from NVD microservice
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{NVD_SERVICE_URL}/api/v1/results/all")
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"NVD service error: {response.status_code} - {response.text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"NVD service error: {response.text}"
                )
                
    except httpx.RequestError as e:
        logger.error(f"Failed to connect to NVD service: {e}")
        raise HTTPException(status_code=503, detail="NVD service unavailable")
    except Exception as e:
        logger.error(f"Unexpected error in get_all_results: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/nvd/results/{job_id}")
async def get_job_result(job_id: str) -> Dict[str, Any]:
    """
    Get specific job result from NVD microservice
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{NVD_SERVICE_URL}/api/v1/queue/job/{job_id}")
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
            else:
                logger.error(f"NVD service error: {response.status_code} - {response.text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"NVD service error: {response.text}"
                )
                
    except httpx.RequestError as e:
        logger.error(f"Failed to connect to NVD service: {e}")
        raise HTTPException(status_code=503, detail="NVD service unavailable")
    except Exception as e:
        logger.error(f"Unexpected error in get_job_result: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/nvd/queue/status")
async def get_queue_status() -> Dict[str, Any]:
    """
    Get queue status from NVD microservice
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{NVD_SERVICE_URL}/api/v1/queue/status")
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"NVD service error: {response.status_code} - {response.text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"NVD service error: {response.text}"
                )
                
    except httpx.RequestError as e:
        logger.error(f"Failed to connect to NVD service: {e}")
        raise HTTPException(status_code=503, detail="NVD service unavailable")
    except Exception as e:
        logger.error(f"Unexpected error in get_queue_status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/nvd/queue/consumer/start")
async def start_consumer() -> Dict[str, Any]:
    """
    Start queue consumer
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(f"{NVD_SERVICE_URL}/api/v1/queue/consumer/start")
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"NVD service error: {response.status_code} - {response.text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"NVD service error: {response.text}"
                )
                
    except httpx.RequestError as e:
        logger.error(f"Failed to connect to NVD service: {e}")
        raise HTTPException(status_code=503, detail="NVD service unavailable")
    except Exception as e:
        logger.error(f"Unexpected error in start_consumer: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/nvd/queue/consumer/stop")
async def stop_consumer() -> Dict[str, Any]:
    """
    Stop queue consumer
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(f"{NVD_SERVICE_URL}/api/v1/queue/consumer/stop")
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"NVD service error: {response.status_code} - {response.text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"NVD service error: {response.text}"
                )
                
    except httpx.RequestError as e:
        logger.error(f"Failed to connect to NVD service: {e}")
        raise HTTPException(status_code=503, detail="NVD service unavailable")
    except Exception as e:
        logger.error(f"Unexpected error in stop_consumer: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/nvd/health")
async def health_check() -> Dict[str, Any]:
    """
    Health check for NVD service
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{NVD_SERVICE_URL}/api/v1/health")
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "status": "unhealthy",
                    "service": "nvd_service",
                    "error": f"HTTP {response.status_code}"
                }
                
    except Exception as e:
        logger.error(f"NVD service health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "nvd_service",
            "error": str(e)
        }
