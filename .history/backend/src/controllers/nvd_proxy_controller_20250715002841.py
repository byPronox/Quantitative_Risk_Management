"""
NVD Proxy Controller - Routes requests to NVD microservice
"""
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Request, Query

from services.nvd_service import NVDService

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize NVD service
nvd_service = NVDService()


@router.get("/nvd/results/all")
async def get_all_results() -> Dict[str, Any]:
    """
    Get all job results from NVD microservice
    """
    try:
        # For now, we'll create a basic NVD service that calls the microservice
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{settings.NVD_SERVICE_URL}/api/v1/results/all")
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"NVD service returned status {response.status_code}")
                raise HTTPException(
                    status_code=response.status_code, 
                    detail=f"NVD service error: {response.text}"
                )
                
    except httpx.RequestError as e:
        logger.error(f"Failed to connect to NVD service: {e}")
        raise HTTPException(
            status_code=503, 
            detail="NVD service unavailable"
        )
    except Exception as e:
        logger.error(f"Unexpected error in get_all_results: {e}")
        raise HTTPException(
            status_code=500, 
            detail="Internal server error"
        )


@router.get("/nvd/queue/status")
async def get_queue_status() -> Dict[str, Any]:
    """
    Get queue status from NVD microservice
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{settings.NVD_SERVICE_URL}/api/v1/queue/status")
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"NVD service returned status {response.status_code}")
                raise HTTPException(
                    status_code=response.status_code, 
                    detail=f"NVD service error: {response.text}"
                )
                
    except httpx.RequestError as e:
        logger.error(f"Failed to connect to NVD service: {e}")
        raise HTTPException(
            status_code=503, 
            detail="NVD service unavailable"
        )
    except Exception as e:
        logger.error(f"Unexpected error in get_queue_status: {e}")
        raise HTTPException(
            status_code=500, 
            detail="Internal server error"
        )


@router.post("/nvd/queue/submit")
async def submit_queue_job(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Submit a job to NVD queue microservice
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{settings.NVD_SERVICE_URL}/api/v1/queue/submit",
                json=request
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"NVD service returned status {response.status_code}")
                raise HTTPException(
                    status_code=response.status_code, 
                    detail=f"NVD service error: {response.text}"
                )
                
    except httpx.RequestError as e:
        logger.error(f"Failed to connect to NVD service: {e}")
        raise HTTPException(
            status_code=503, 
            detail="NVD service unavailable"
        )
    except Exception as e:
        logger.error(f"Unexpected error in submit_queue_job: {e}")
        raise HTTPException(
            status_code=500, 
            detail="Internal server error"
        )


@router.post("/nvd/vulnerabilities/search")
async def search_vulnerabilities(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Search vulnerabilities using NVD microservice
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{settings.NVD_SERVICE_URL}/api/v1/vulnerabilities/search",
                json=request
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"NVD service returned status {response.status_code}")
                raise HTTPException(
                    status_code=response.status_code, 
                    detail=f"NVD service error: {response.text}"
                )
                
    except httpx.RequestError as e:
        logger.error(f"Failed to connect to NVD service: {e}")
        raise HTTPException(
            status_code=503, 
            detail="NVD service unavailable"
        )
    except Exception as e:
        logger.error(f"Unexpected error in search_vulnerabilities: {e}")
        raise HTTPException(
            status_code=500, 
            detail="Internal server error"
        )


@router.post("/nvd/risk/analyze")
async def analyze_risk(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Perform risk analysis using NVD microservice
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{settings.NVD_SERVICE_URL}/api/v1/risk/analyze",
                json=request
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"NVD service returned status {response.status_code}")
                raise HTTPException(
                    status_code=response.status_code, 
                    detail=f"NVD service error: {response.text}"
                )
                
    except httpx.RequestError as e:
        logger.error(f"Failed to connect to NVD service: {e}")
        raise HTTPException(
            status_code=503, 
            detail="NVD service unavailable"
        )
    except Exception as e:
        logger.error(f"Unexpected error in analyze_risk: {e}")
        raise HTTPException(
            status_code=500, 
            detail="Internal server error"
        )


@router.get("/nvd/results/{job_id}")
async def get_job_results(job_id: str) -> Dict[str, Any]:
    """
    Get specific job results from NVD microservice
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{settings.NVD_SERVICE_URL}/api/v1/results/{job_id}")
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"NVD service returned status {response.status_code}")
                raise HTTPException(
                    status_code=response.status_code, 
                    detail=f"NVD service error: {response.text}"
                )
                
    except httpx.RequestError as e:
        logger.error(f"Failed to connect to NVD service: {e}")
        raise HTTPException(
            status_code=503, 
            detail="NVD service unavailable"
        )
    except Exception as e:
        logger.error(f"Unexpected error in get_job_results: {e}")
        raise HTTPException(
            status_code=500, 
            detail="Internal server error"
        )


@router.get("/nvd/health")
async def nvd_health_check() -> Dict[str, Any]:
    """
    Health check endpoint for NVD microservice
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{settings.NVD_SERVICE_URL}/api/v1/health")
            
            if response.status_code == 200:
                nvd_status = response.json()
                return {
                    "nvd_service": "available",
                    "nvd_service_response": nvd_status,
                    "gateway": "ok"
                }
            else:
                return {
                    "nvd_service": "unavailable",
                    "nvd_service_status": response.status_code,
                    "gateway": "ok"
                }
                
    except Exception as e:
        logger.error(f"NVD service health check failed: {e}")
        return {
            "nvd_service": "unavailable",
            "error": str(e),
            "gateway": "ok"
        }
