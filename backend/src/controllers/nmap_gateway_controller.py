"""
Nmap Gateway Controller
Proxy endpoints for Nmap Scanner Service
"""
import httpx
import logging
from fastapi import APIRouter, HTTPException
from typing import Optional
import os

logger = logging.getLogger(__name__)

router = APIRouter()

# Nmap service URL from environment variable
NMAP_SERVICE_URL = os.getenv("NMAP_SERVICE_URL", "http://nmap-scanner-service:8004")

@router.post("/nmap/queue/job")
async def add_nmap_job_to_queue(target_ip: str):
    """Proxy endpoint to add Nmap scan job to queue"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{NMAP_SERVICE_URL}/api/v1/queue/job",
                params={"target_ip": target_ip}
            )
            return response.json()
    except Exception as e:
        logger.error(f"Error proxying to Nmap service: {e}")
        raise HTTPException(status_code=503, detail="Nmap service unavailable")

@router.get("/nmap/queue/status")
async def get_nmap_queue_status():
    """Proxy endpoint to get Nmap queue status"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{NMAP_SERVICE_URL}/api/v1/queue/status")
            return response.json()
    except Exception as e:
        logger.error(f"Error proxying to Nmap service: {e}")
        raise HTTPException(status_code=503, detail="Nmap service unavailable")

@router.get("/nmap/queue/results/all")
async def get_all_nmap_queue_results():
    """Proxy endpoint to get all Nmap queue results"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{NMAP_SERVICE_URL}/api/v1/queue/results/all")
            return response.json()
    except Exception as e:
        logger.error(f"Error proxying to Nmap service: {e}")
        raise HTTPException(status_code=503, detail="Nmap service unavailable")

@router.get("/nmap/queue/results/{job_id}")
async def get_nmap_job_result(job_id: str):
    """Proxy endpoint to get specific Nmap job result"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{NMAP_SERVICE_URL}/api/v1/queue/results/{job_id}")
            return response.json()
    except Exception as e:
        logger.error(f"Error proxying to Nmap service: {e}")
        raise HTTPException(status_code=503, detail="Nmap service unavailable")

@router.get("/nmap/database/jobs")
async def get_nmap_database_jobs():
    """Proxy endpoint to get all Nmap jobs from database"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{NMAP_SERVICE_URL}/api/v1/database/jobs")
            return response.json()
    except Exception as e:
        logger.error(f"Error proxying to Nmap service: {e}")
        raise HTTPException(status_code=503, detail="Nmap service unavailable")

@router.get("/nmap/database/results/{job_id}")
async def get_nmap_scan_results(job_id: str):
    """Proxy endpoint to get Nmap scan results for a specific job"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{NMAP_SERVICE_URL}/api/v1/database/results/{job_id}")
            return response.json()
    except Exception as e:
        logger.error(f"Error proxying to Nmap service: {e}")
        raise HTTPException(status_code=503, detail="Nmap service unavailable")

@router.post("/nmap/queue/consumer/start")
async def start_nmap_consumer():
    """Proxy endpoint to start Nmap consumer"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(f"{NMAP_SERVICE_URL}/api/v1/queue/consumer/start")
            return response.json()
    except Exception as e:
        logger.error(f"Error proxying to Nmap service: {e}")
        raise HTTPException(status_code=503, detail="Nmap service unavailable")

@router.post("/nmap/queue/consumer/stop")
async def stop_nmap_consumer():
    """Proxy endpoint to stop Nmap consumer"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(f"{NMAP_SERVICE_URL}/api/v1/queue/consumer/stop")
            return response.json()
    except Exception as e:
        logger.error(f"Error proxying to Nmap service: {e}")
        raise HTTPException(status_code=503, detail="Nmap service unavailable")

@router.get("/nmap/queue/consumer/status")
async def get_nmap_consumer_status():
    """Proxy endpoint to get Nmap consumer status"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{NMAP_SERVICE_URL}/api/v1/queue/consumer/status")
            return response.json()
    except Exception as e:
        logger.error(f"Error proxying to Nmap service: {e}")
        raise HTTPException(status_code=503, detail="Nmap service unavailable")

@router.get("/nmap/health")
async def nmap_health_check():
    """Proxy endpoint for Nmap service health check"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{NMAP_SERVICE_URL}/api/v1/health")
            return response.json()
    except Exception as e:
        logger.error(f"Error proxying to Nmap service: {e}")
        raise HTTPException(status_code=503, detail="Nmap service unavailable")
