"""
Nmap Scanner Controller - Integration with QRMS Backend
"""
import httpx
import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import asyncio

from config.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic models for request/response
class ScanRequest(BaseModel):
    ip: str = Field(..., description="IP address or hostname to scan")
    
class ScanResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    details: Optional[str] = None
    scanDuration: Optional[str] = None
    timestamp: str

class ValidationRequest(BaseModel):
    target: str = Field(..., description="IP address or hostname to validate")

class ValidationResponse(BaseModel):
    target: str
    isValidIP: bool
    isValidHostname: bool
    isValid: bool
    timestamp: str

# HTTP client for nmap service
nmap_service_url = f"http://nmap-scanner-service:8004"

async def get_nmap_service_client():
    """Get HTTP client for nmap service"""
    return httpx.AsyncClient(
        base_url=nmap_service_url,
        timeout=httpx.Timeout(300.0)  # 5 minutes timeout
    )

@router.post("/nmap/scan", response_model=ScanResponse)
async def scan_target(request: ScanRequest):
    """
    Scan a target IP or hostname using nmap
    
    Executes: nmap -sV --script vuln [IP] -oX scan_result.xml
    """
    logger.info(f"Received scan request for target: {request.ip}")
    
    try:
        async with await get_nmap_service_client() as client:
            response = await client.post(
                "/api/v1/scan",
                json={"ip": request.ip}
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Scan completed successfully for {request.ip}")
                return ScanResponse(**result)
            else:
                error_data = response.json()
                logger.error(f"Scan failed for {request.ip}: {error_data}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=error_data
                )
                
    except httpx.TimeoutException:
        logger.error(f"Scan timeout for {request.ip}")
        raise HTTPException(
            status_code=408,
            detail={
                "error": "Scan timeout",
                "details": "Nmap scan exceeded 5 minute timeout",
                "target": request.ip
            }
        )
    except httpx.ConnectError:
        logger.error("Cannot connect to nmap scanner service")
        raise HTTPException(
            status_code=503,
            detail={
                "error": "Service unavailable",
                "details": "Nmap scanner service is not available"
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error during scan: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "details": str(e)
            }
        )

@router.get("/nmap/test")
async def test_nmap_service():
    """Test nmap service installation and availability"""
    logger.info("Testing nmap service...")
    
    try:
        async with await get_nmap_service_client() as client:
            response = await client.get("/api/v1/test")
            
            if response.status_code == 200:
                result = response.json()
                logger.info("Nmap service test successful")
                return result
            else:
                error_data = response.json()
                logger.error(f"Nmap service test failed: {error_data}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=error_data
                )
                
    except httpx.ConnectError:
        logger.error("Cannot connect to nmap scanner service")
        raise HTTPException(
            status_code=503,
            detail={
                "error": "Service unavailable",
                "details": "Nmap scanner service is not available"
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error during nmap test: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "details": str(e)
            }
        )

@router.get("/nmap/validate/{target}", response_model=ValidationResponse)
async def validate_target(target: str):
    """Validate IP address or hostname format"""
    logger.info(f"Validating target: {target}")
    
    try:
        async with await get_nmap_service_client() as client:
            response = await client.get(f"/api/v1/validate/{target}")
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Target validation completed for {target}")
                return ValidationResponse(**result)
            else:
                error_data = response.json()
                logger.error(f"Target validation failed for {target}: {error_data}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=error_data
                )
                
    except httpx.ConnectError:
        logger.error("Cannot connect to nmap scanner service")
        raise HTTPException(
            status_code=503,
            detail={
                "error": "Service unavailable",
                "details": "Nmap scanner service is not available"
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error during target validation: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "details": str(e)
            }
        )

@router.get("/nmap/status")
async def get_nmap_status():
    """Get nmap service status and configuration"""
    logger.info("Getting nmap service status...")
    
    try:
        async with await get_nmap_service_client() as client:
            response = await client.get("/api/v1/status")
            
            if response.status_code == 200:
                result = response.json()
                logger.info("Nmap service status retrieved successfully")
                return result
            else:
                error_data = response.json()
                logger.error(f"Failed to get nmap service status: {error_data}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=error_data
                )
                
    except httpx.ConnectError:
        logger.error("Cannot connect to nmap scanner service")
        raise HTTPException(
            status_code=503,
            detail={
                "error": "Service unavailable",
                "details": "Nmap scanner service is not available"
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error getting nmap status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "details": str(e)
            }
        )

@router.get("/nmap/scripts")
async def get_nmap_scripts():
    """Get available nmap vulnerability scripts"""
    logger.info("Getting available nmap scripts...")
    
    try:
        async with await get_nmap_service_client() as client:
            response = await client.get("/api/v1/scripts")
            
            if response.status_code == 200:
                result = response.json()
                logger.info("Nmap scripts retrieved successfully")
                return result
            else:
                error_data = response.json()
                logger.error(f"Failed to get nmap scripts: {error_data}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=error_data
                )
                
    except httpx.ConnectError:
        logger.error("Cannot connect to nmap scanner service")
        raise HTTPException(
            status_code=503,
            detail={
                "error": "Service unavailable",
                "details": "Nmap scanner service is not available"
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error getting nmap scripts: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "details": str(e)
            }
        )

@router.get("/nmap/health")
async def nmap_health_check():
    """Health check for nmap service"""
    logger.info("Performing nmap service health check...")
    
    try:
        async with await get_nmap_service_client() as client:
            response = await client.get("/api/v1/health")
            
            if response.status_code == 200:
                result = response.json()
                logger.info("Nmap service health check passed")
                return result
            else:
                error_data = response.json()
                logger.error(f"Nmap service health check failed: {error_data}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=error_data
                )
                
    except httpx.ConnectError:
        logger.error("Cannot connect to nmap scanner service")
        raise HTTPException(
            status_code=503,
            detail={
                "error": "Service unavailable",
                "details": "Nmap scanner service is not available"
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error during nmap health check: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "details": str(e)
            }
        )
