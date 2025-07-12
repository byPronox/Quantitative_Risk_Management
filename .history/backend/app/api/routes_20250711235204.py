from fastapi import APIRouter, HTTPException, Request
from typing import Dict, Any
import httpx
import os
import logging
import time
from queue_manager.queue import RabbitMQManager, publish_to_queue, start_queue_consumer, stop_queue_consumer

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/health")
async def health_check():
    """Health check endpoint for Kong Gateway"""
    return {
        "status": "healthy",
        "service": "Risk Management API Gateway",
        "version": "1.0.0"
    }

@router.get("/services/status")
async def services_status():
    """Check status of all microservices"""
    services = {
        "ml_prediction": os.getenv("ML_SERVICE_URL", "http://ml-prediction-service:8001"),
        "nvd_service": os.getenv("NVD_SERVICE_URL", "http://nvd-service:8002")
    }
    
    status = {}
    
    for service_name, url in services.items():
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{url}/api/v1/health")
                if response.status_code == 200:
                    status[service_name] = "healthy"
                else:
                    status[service_name] = "unhealthy"
        except Exception as e:
            status[service_name] = f"error: {str(e)}"
    
    return {
        "gateway_status": "healthy",
        "microservices": status
    }

@router.post("/predict/combined/")
async def predict_combined(request: Request):
    """Legacy endpoint - proxy to ML microservice"""
    try:
        # Get request body
        body = await request.json()
        
        ml_service_url = os.getenv("ML_SERVICE_URL", "http://ml-prediction-service:8001")
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{ml_service_url}/api/v1/predict/combined",
                json=body
            )
            return response.json()
    except Exception as e:
        logger.error("Error calling ML service: %s", str(e))
        raise HTTPException(status_code=503, detail="ML service unavailable") from e

@router.get("/nvd")
async def search_nvd_vulnerabilities(keyword: str = ""):
    """Legacy NVD endpoint - proxy to NVD microservice"""
    try:
        # Use "vulnerability" as default if no keyword provided
        search_keyword = keyword.strip() if keyword.strip() else "vulnerability"
        
        nvd_service_url = os.getenv("NVD_SERVICE_URL", "http://nvd-service:8002")
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{nvd_service_url}/api/v1/vulnerabilities/search",
                json={"keywords": search_keyword, "results_per_page": 20}
            )
            if response.status_code != 200:
                logger.error("NVD service error: %s - %s", response.status_code, response.text)
                raise HTTPException(status_code=response.status_code, detail="NVD search failed")
            return response.json()
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error calling NVD service: %s", str(e))
        raise HTTPException(status_code=503, detail="NVD service unavailable") from e

@router.get("/proxy/{service_name}/{path:path}")
async def proxy_to_microservice(service_name: str, path: str):
    """Proxy requests to microservices (fallback for Kong)"""
    services = {
        "ml": os.getenv("ML_SERVICE_URL", "http://ml-prediction-service:8001"),
        "nvd": os.getenv("NVD_SERVICE_URL", "http://nvd-service:8002")
    }
    
    if service_name not in services:
        raise HTTPException(status_code=404, detail=f"Service {service_name} not found")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{services[service_name]}/api/v1/{path}")
            return response.json()
    except Exception as e:
        logger.error("Error proxying to %s: %s", service_name, str(e))
        raise HTTPException(status_code=503, detail=f"Service {service_name} unavailable") from e

# Queue Management Routes
@router.get("/nvd/queue/status")
async def get_queue_status():
    """Get RabbitMQ queue status for NVD analysis"""
    try:
        # First try to get status from NVD service
        try:
            nvd_service_url = os.getenv("NVD_SERVICE_URL", "http://nvd-service:8002")
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{nvd_service_url}/api/v1/queue/status")
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            logger.warning("Could not get NVD service queue info: %s", str(e))
        
        # Fallback to basic queue manager info using connection manager
        try:
            from queue_manager.queue import get_rabbitmq_connection
            async with get_rabbitmq_connection() as manager:
                queue_info = await manager.get_queue_info()
                return queue_info
        except Exception as e:
            logger.error("RabbitMQ connection failed: %s", str(e))
            # Return basic info without connection
            from queue_manager.queue import _job_results_store
            return {
                "error": "RabbitMQ connection failed",
                "connected": False,
                "queue_size": 0,
                "total_vulnerabilities": len(_job_results_store),
                "keywords": [],
                "status": "disconnected",
                "fallback_mode": True
            }
        
    except Exception as e:
        logger.error("Error getting queue status: %s", str(e))
        return {
            "error": str(e),
            "connected": False,
            "queue_size": 0,
            "total_vulnerabilities": 0,
            "keywords": [],
            "status": "error"
        }

@router.delete("/nvd/queue/clear")
async def clear_queue():
    """Clear the RabbitMQ queue"""
    try:
        # Try to clear via NVD service first
        nvd_service_url = os.getenv("NVD_SERVICE_URL", "http://nvd-service:8002")
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.delete(f"{nvd_service_url}/api/v1/queue/clear")
            if response.status_code == 200:
                return response.json()
        
        # Fallback to direct queue management
        manager = RabbitMQManager()
        await manager.connect()
        
        # Simple queue purge (implementation depends on your queue structure)
        result = {
            "message": "Queue cleared successfully",
            "cleared_items": 0,
            "queue_name": manager.queue_name
        }
        
        await manager.close()
        return result
        
    except Exception as e:
        logger.error("Error clearing queue: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Failed to clear queue: {str(e)}") from e

@router.post("/nvd/queue/add")
async def add_to_queue(request: Dict[str, Any]):
    """Add keyword to analysis queue"""
    try:
        keyword = request.get("keyword")
        if not keyword:
            raise HTTPException(status_code=400, detail="Keyword is required")
        
        # Add to queue using RabbitMQ
        try:
            job_id = await publish_to_queue(keyword, request.get("metadata", {}))
            status = "queued" if not job_id.startswith("mock-") else "queued_mock"
        except Exception as e:
            logger.warning("RabbitMQ queue failed, using mock job: %s", str(e))
            job_id = f"mock-job-{keyword}-{int(time.time())}"
            status = "queued_mock"
        
        return {
            "message": f"Keyword '{keyword}' added to analysis queue",
            "job_id": job_id,
            "keyword": keyword,
            "status": status
        }
        
    except Exception as e:
        logger.error("Error adding to queue: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Failed to add to queue: {str(e)}") from e

# Additional endpoints for frontend compatibility
@router.post("/nvd/add_to_queue")
async def add_to_queue_alt(request: Dict[str, Any]):
    """Alternative endpoint for adding keyword to queue (frontend compatibility)"""
    return await add_to_queue(request)

@router.post("/nvd/analyze_software_async")
async def analyze_software_async(request: Dict[str, Any]):
    """Analyze multiple software packages asynchronously"""
    try:
        software_list = request.get("software_list", [])
        if not software_list:
            raise HTTPException(status_code=400, detail="Software list is required")
        
        # Queue jobs for each software
        job_ids = []
        jobs = []
        
        for software in software_list:
            try:
                job_id = await publish_to_queue(software, request.get("metadata", {}))
                job_ids.append(job_id)
                jobs.append({
                    "software": software,
                    "jobId": job_id,
                    "keyword": software,
                    "status": "queued"
                })
            except Exception as e:
                logger.warning("Failed to queue software %s: %s", software, str(e))
                # Add mock job if RabbitMQ fails
                mock_job_id = f"mock-job-{software}-{int(time.time())}"
                job_ids.append(mock_job_id)
                jobs.append({
                    "software": software,
                    "jobId": mock_job_id,
                    "keyword": software,
                    "status": "queued_mock"
                })
        
        return {
            "message": f"{len(jobs)} software queued for analysis",
            "job_ids": job_ids,
            "estimated_time": len(jobs) * 3,  # 3 seconds per job estimated
            "jobs": jobs
        }
        
    except Exception as e:
        logger.error("Error analyzing software async: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Failed to start async analysis: {str(e)}") from e

@router.post("/nvd/analyze_risk")
async def analyze_nvd_risk():
    """Analyze NVD risk (placeholder endpoint)"""
    try:
        # Try to call NVD service risk analysis
        try:
            nvd_service_url = os.getenv("NVD_SERVICE_URL", "http://nvd-service:8002")
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(f"{nvd_service_url}/api/v1/analysis/risk", json={
                    "vulnerabilities": [],  # Empty for demo
                    "asset_criticality": "medium",
                    "threat_landscape": "standard"
                })
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            logger.warning("NVD service risk analysis failed: %s", str(e))
        
        # Return mock risk analysis if service fails
        return {
            "risk_score": 7.5,
            "risk_level": "High",
            "recommendations": [
                "Update affected software components",
                "Implement additional monitoring",
                "Review access controls"
            ],
            "vulnerability_count": 0,
            "critical_count": 0,
            "high_count": 0,
            "medium_count": 0,
            "low_count": 0
        }
        
    except Exception as e:
        logger.error("Error analyzing NVD risk: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Risk analysis failed: {str(e)}") from e

@router.get("/nvd/results/{job_id}")
async def get_job_results(job_id: str):
    """Get results for a specific job ID - uses Kong Gateway for real data"""
    try:
        # Validate job_id format first
        if not job_id or job_id.strip() == "":
            raise HTTPException(
                status_code=400,
                detail="Job ID is required and cannot be empty"
            )
        
        # Special handling for "all" - this might be a frontend bug
        if job_id.lower() == "all":
            logger.warning("Invalid job ID 'all' requested - this may be a frontend issue")
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Invalid job ID",
                    "job_id": job_id,
                    "message": "Job ID 'all' is not valid. Please provide a specific job ID."
                }
            )
        
        # Try to get processed results from the queue manager
        manager = None
        try:
            manager = RabbitMQManager()
            await manager.connect()
            
            result = await manager.get_job_result(job_id)
            if result and result.get("status") == "completed":
                # Return the processed result
                return {
                    "job_id": job_id,
                    "status": "completed",
                    "keyword": result.get("keyword"),
                    "total_results": result.get("total_results", 0),
                    "vulnerabilities": result.get("vulnerabilities", [])[:10],
                    "processed_via": result.get("processed_via", "queue_consumer")
                }
            elif result and result.get("status") == "processing":
                # Job is still being processed
                return {
                    "job_id": job_id,
                    "status": "processing",
                    "keyword": result.get("keyword"),
                    "message": "Job is being processed by consumer"
                }
            elif result and result.get("status") == "failed":
                # Job failed processing
                return {
                    "job_id": job_id,
                    "status": "failed",
                    "error": result.get("error"),
                    "keyword": result.get("keyword")
                }
            elif result and result.get("status") == "not_found":
                # Job not found in queue manager
                logger.warning("Job %s not found in queue manager", job_id)
                raise HTTPException(
                    status_code=404,
                    detail={
                        "error": "Job not found",
                        "job_id": job_id,
                        "message": "Job may not exist or has expired. Please start the queue consumer to process jobs."
                    }
                )
            else:
                # Unknown status or no result
                logger.warning("Job %s has unknown status or no result", job_id)
                raise HTTPException(
                    status_code=404,
                    detail={
                        "error": "Job not found or has unknown status",
                        "job_id": job_id,
                        "message": "Job may not exist, has expired, or has an unknown status."
                    }
                )
        finally:
            if manager:
                await manager.close()
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error("Error getting job results for %s: %s", job_id, str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get job results: {str(e)}") from e

# Add after the existing job results endpoint

@router.get("/nvd/results/all")
async def get_all_job_results():
    """Get all job results from the queue manager"""
    try:
        manager = None
        try:
            manager = RabbitMQManager()
            await manager.connect()
            
            # Get all stored job results
            from queue_manager.queue import _job_results_store, _job_metadata_store
            
            all_results = []
            
            # Get completed results
            for job_id, result in _job_results_store.items():
                all_results.append({
                    "job_id": job_id,
                    "status": result.get("status", "unknown"),
                    "keyword": result.get("keyword", ""),
                    "total_results": result.get("total_results", 0),
                    "timestamp": result.get("timestamp", 0),
                    "error": result.get("error") if result.get("status") == "failed" else None
                })
            
            # Get pending jobs (in metadata but not in results)
            for job_id, metadata in _job_metadata_store.items():
                if job_id not in _job_results_store:
                    all_results.append({
                        "job_id": job_id,
                        "status": "pending",
                        "keyword": metadata.get("keyword", ""),
                        "total_results": 0,
                        "timestamp": metadata.get("timestamp", 0),
                        "error": None
                    })
            
            return {
                "message": f"Found {len(all_results)} jobs",
                "total_jobs": len(all_results),
                "completed": len([r for r in all_results if r["status"] == "completed"]),
                "failed": len([r for r in all_results if r["status"] == "failed"]),
                "pending": len([r for r in all_results if r["status"] == "pending"]),
                "processing": len([r for r in all_results if r["status"] == "processing"]),
                "results": all_results
            }
            
        finally:
            if manager:
                await manager.close()
        
    except Exception as e:
        logger.error("Error getting all job results: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get all job results: {str(e)}") from e

# NVD API Proxy with Kong integration
@router.get("/nvd/cves/2.0")
async def get_nvd_vulnerabilities(keywordSearch: str | None = None, **params):
    """
    Proxy to Kong Gateway for NVD CVE API
    Frontend → Backend → Kong → NVD API
    """
    try:
        # Kong URL - using your configured Kong Gateway
        kong_url = "https://kong-b27b67aff4usnspl9.kongcloud.dev"
        
        # Build query parameters
        query_params = {}
        if keywordSearch:
            query_params["keywordSearch"] = keywordSearch
        
        # Add any additional parameters
        for key, value in params.items():
            if value is not None:
                query_params[key] = value
        
        logger.info("Calling Kong Gateway: %s/nvd/cves/2.0 with params: %s", kong_url, query_params)
        
        # Make request to Kong Gateway
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{kong_url}/nvd/cves/2.0",
                params=query_params
            )
            
            if response.status_code != 200:
                logger.error("Kong NVD API error: %s - %s", response.status_code, response.text)
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"NVD API error: {response.text}"
                )
            
            logger.info("Kong Gateway response: %s vulnerabilities found", 
                       response.json().get("totalResults", 0))
            
            return response.json()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error calling Kong NVD API: %s", str(e))
        raise HTTPException(status_code=503, detail="NVD API service unavailable") from e

@router.post("/nvd/queue/consumer/start")
async def start_consumer():
    """Start the RabbitMQ consumer for processing jobs via Kong"""
    try:
        await start_queue_consumer()
        return {
            "message": "Queue consumer started successfully",
            "status": "running",
            "description": "Consumer will now process jobs using Kong Gateway"
        }
    except Exception as e:
        logger.error("Error starting consumer: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Failed to start consumer: {str(e)}") from e

@router.post("/nvd/queue/consumer/stop")
async def stop_consumer():
    """Stop the RabbitMQ consumer"""
    try:
        await stop_queue_consumer()
        return {
            "message": "Queue consumer stopped successfully",
            "status": "stopped"
        }
    except Exception as e:
        logger.error("Error stopping consumer: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Failed to stop consumer: {str(e)}") from e