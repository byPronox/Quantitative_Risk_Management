from fastapi import APIRouter, HTTPException, Request
from typing import Dict, Any
import httpx
import os
import logging
import time
from datetime import datetime

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
async def proxy_predict_combined(request: Request):
    """Proxy to ML microservice for combined prediction"""
    try:
        body = await request.json()
        ml_service_url = os.getenv("ML_SERVICE_URL", "http://ml-prediction-service:8001")
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{ml_service_url}/api/v1/predict/combined",
                json=body
            )
            if response.status_code != 200:
                logger.error("ML service error: %s - %s", response.status_code, response.text)
                raise HTTPException(status_code=response.status_code, detail="ML prediction failed")
            return response.json()
    except Exception as e:
        logger.error("Error proxying to ML service: %s", str(e))
        raise HTTPException(status_code=503, detail="ML service unavailable") from e

@router.get("/nvd")
async def proxy_nvd(keyword: str = ""):
    """Proxy to Kong Gateway for vulnerability search (GET /nvd/cves/2.0)"""
    try:
        kong_url = os.getenv("KONG_URL", "https://kong-b27b67aff4usnspl9.kongcloud.dev")
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{kong_url}/nvd/cves/2.0",
                params={"keywordSearch": keyword.strip() if keyword.strip() else "vulnerability", "resultsPerPage": 20}
            )
            if response.status_code != 200:
                logger.error("Kong NVD service error: %s - %s", response.status_code, response.text)
                raise HTTPException(status_code=response.status_code, detail="NVD search via Kong failed")
            return response.json()
    except Exception as e:
        logger.error("Error proxying to Kong NVD service: %s", str(e))
        raise HTTPException(status_code=503, detail="NVD service unavailable") from e

@router.get("/nvd/results/{job_id}")
async def proxy_nvd_job_result(job_id: str):
    """Proxy to NVD microservice for a specific job result (async analysis)"""
    try:
        nvd_service_url = os.getenv("NVD_SERVICE_URL", "http://nvd-service:8002")
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{nvd_service_url}/api/v1/results/{job_id}")
            if response.status_code == 404:
                return {
                    "job_id": job_id,
                    "status": "queued",
                    "message": "Job is still queued or processing."
                }
            return response.json()
    except Exception as e:
        logger.error("Error proxying to NVD service (results/{job_id}): %s", str(e))
        raise HTTPException(status_code=503, detail="NVD service unavailable") from e

@router.get("/nvd/queue/status")
async def proxy_nvd_queue_status():
    """Proxy to NVD microservice for queue status"""
    try:
        nvd_service_url = os.getenv("NVD_SERVICE_URL", "http://nvd-service:8002")
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{nvd_service_url}/api/v1/queue/status")
            return response.json()
    except Exception as e:
        logger.error("Error proxying to NVD service (queue/status): %s", str(e))
        raise HTTPException(status_code=503, detail="NVD service unavailable") from e

@router.post("/nvd/analyze_software_async")
async def proxy_nvd_analyze_software_async(request: Request):
    """Proxy to NVD microservice for asynchronous software analysis"""
    try:
        body = await request.json()
        nvd_service_url = os.getenv("NVD_SERVICE_URL", "http://nvd-service:8002")
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(f"{nvd_service_url}/api/v1/analyze_software_async", json=body)
            return response.json()
    except Exception as e:
        logger.error("Error proxying to NVD service (analyze_software_async): %s", str(e))
        raise HTTPException(status_code=503, detail="NVD service unavailable") from e

@router.get("/nvd/results/all")
async def proxy_nvd_results_all():
    """Proxy to NVD microservice for retrieving all results and save to MongoDB"""
    try:
        nvd_service_url = os.getenv("NVD_SERVICE_URL", "http://nvd-service:8002")
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{nvd_service_url}/api/v1/results/all")
            results_data = response.json()
            
            # Guardar automáticamente en MongoDB si hay trabajos completados
            if results_data.get("success") and results_data.get("jobs"):
                await save_results_to_mongodb(results_data["jobs"])
            
            return results_data
    except Exception as e:
        logger.error("Error proxying to NVD service (results/all): %s", str(e))
        raise HTTPException(status_code=503, detail="NVD service unavailable") from e

async def save_results_to_mongodb(jobs_data):
    """Guarda los resultados de trabajos NVD en MongoDB con tu estructura"""
    try:
        from ..database.mongodb import MongoDBConnection
        from datetime import datetime
        
        # Conectar a MongoDB
        mongodb = MongoDBConnection()
        await mongodb.connect()
        
        for job in jobs_data:
            if job.get("status") == "completed" and job.get("vulnerabilities"):
                # Convertir la estructura para tu schema de MongoDB
                job_document = {
                    "job_id": job.get("job_id", ""),
                    "keyword": job.get("keyword", ""),
                    "status": job.get("status", "pending"),
                    "total_results": int(job.get("total_results", 0)),
                    "processed_at": float(job.get("timestamp", time.time())),
                    "processed_via": job.get("processed_via", "kong_gateway"),
                    "vulnerabilities": []
                }
                
                # Procesar cada vulnerabilidad según tu estructura
                for vuln in job.get("vulnerabilities", []):
                    if "cve" in vuln:
                        cve_data = vuln["cve"]
                        processed_vuln = {
                            "cve": {
                                "id": cve_data.get("id", ""),
                                "sourceIdentifier": cve_data.get("sourceIdentifier", ""),
                                "published": datetime.fromisoformat(cve_data.get("published", "1970-01-01T00:00:00.000").replace("Z", "+00:00")) if cve_data.get("published") else datetime(1970, 1, 1),
                                "lastModified": datetime.fromisoformat(cve_data.get("lastModified", "1970-01-01T00:00:00.000").replace("Z", "+00:00")) if cve_data.get("lastModified") else datetime(1970, 1, 1),
                                "vulnStatus": cve_data.get("vulnStatus", "Unknown"),
                                "cveTags": cve_data.get("cveTags", []),
                                "descriptions": cve_data.get("descriptions", []),
                                "metrics": cve_data.get("metrics", {}),
                                "weaknesses": cve_data.get("weaknesses", []),
                                "configurations": cve_data.get("configurations", []),
                                "references": cve_data.get("references", []),
                                "vendorComments": cve_data.get("vendorComments", [])
                            }
                        }
                        job_document["vulnerabilities"].append(processed_vuln)
                
                # Insertar o actualizar en MongoDB (usar upsert por job_id)
                await mongodb.db.jobs.update_one(
                    {"job_id": job_document["job_id"]},
                    {"$set": job_document},
                    upsert=True
                )
                
                logger.info(f"Guardado job {job_document['job_id']} con {len(job_document['vulnerabilities'])} vulnerabilidades en MongoDB cveScanner.jobs")
        
        await mongodb.disconnect()
        logger.info(f"Proceso de guardado en MongoDB completado para {len(jobs_data)} trabajos")
        
    except Exception as e:
        logger.error(f"Error guardando en MongoDB: {e}")
        # No lanzar excepción para no romper la respuesta principal

@router.post("/nvd/consumer/start")
async def proxy_nvd_consumer_start():
    """Proxy to NVD microservice to start the consumer (process jobs from queue)"""
    try:
        nvd_service_url = os.getenv("NVD_SERVICE_URL", "http://nvd-service:8002")
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(f"{nvd_service_url}/api/v1/consumer/start")
            return response.json()
    except Exception as e:
        logger.error("Error proxying to NVD service (consumer/start): %s", str(e))
        raise HTTPException(status_code=503, detail="NVD service unavailable") from e

@router.post("/nvd/consumer/stop")
async def proxy_nvd_consumer_stop():
    """Proxy to NVD microservice to stop the consumer"""
    try:
        nvd_service_url = os.getenv("NVD_SERVICE_URL", "http://nvd-service:8002")
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(f"{nvd_service_url}/api/v1/consumer/stop")
            return response.json()
    except Exception as e:
        logger.error("Error proxying to NVD service (consumer/stop): %s", str(e))
        raise HTTPException(status_code=503, detail="NVD service unavailable") from e

@router.post("/nvd/queue/consumer/start")
async def proxy_nvd_queue_consumer_start():
    """Alias para iniciar el consumidor de la cola NVD (compatibilidad frontend)"""
    try:
        nvd_service_url = os.getenv("NVD_SERVICE_URL", "http://nvd-service:8002")
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(f"{nvd_service_url}/api/v1/consumer/start")
            return response.json()
    except Exception as e:
        logger.error("Error proxying to NVD service (queue/consumer/start): %s", str(e))
        raise HTTPException(status_code=503, detail="NVD service unavailable") from e

@router.post("/nvd/queue/consumer/stop")
async def proxy_nvd_queue_consumer_stop():
    """Alias para detener el consumidor de la cola NVD (compatibilidad frontend)"""
    try:
        nvd_service_url = os.getenv("NVD_SERVICE_URL", "http://nvd-service:8002")
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(f"{nvd_service_url}/api/v1/consumer/stop")
            return response.json()
    except Exception as e:
        logger.error("Error proxying to NVD service (queue/consumer/stop): %s", str(e))
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

@router.get("/nvd/results/mongodb")
async def get_nvd_results_from_mongodb():
    """Obtener todos los resultados guardados en MongoDB cveScanner.jobs"""
    try:
        from ..database.mongodb_connection import MongoDBConnection
        
        # Conectar a MongoDB
        mongodb = MongoDBConnection()
        await mongodb.connect()
        
        # Consultar todos los trabajos guardados
        cursor = mongodb.db.jobs.find({}).sort("processed_at", -1)
        results = []
        
        async for doc in cursor:
            # Convertir ObjectId a string para serialización JSON
            doc["_id"] = str(doc["_id"])
            
            # Convertir datetime a timestamp para compatibilidad
            if "processed_at" in doc and isinstance(doc["processed_at"], datetime):
                doc["processed_at"] = doc["processed_at"].timestamp()
            
            results.append(doc)
        
        await mongodb.disconnect()
        
        return {
            "success": True,
            "total_jobs": len(results),
            "source": "mongodb_cveScanner_jobs",
            "jobs": results
        }
        
    except Exception as e:
        logger.error(f"Error consultando MongoDB: {e}")
        return {
            "success": False,
            "error": str(e),
            "total_jobs": 0,
            "jobs": []
        }

@router.post("/nvd/consumer/start")
async def proxy_nvd_consumer_start():
    """Proxy to NVD microservice to start the consumer (process jobs from queue)"""
    try:
        nvd_service_url = os.getenv("NVD_SERVICE_URL", "http://nvd-service:8002")
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(f"{nvd_service_url}/api/v1/consumer/start")
            return response.json()
    except Exception as e:
        logger.error("Error proxying to NVD service (consumer/start): %s", str(e))
        raise HTTPException(status_code=503, detail="NVD service unavailable") from e

@router.post("/nvd/consumer/stop")
async def proxy_nvd_consumer_stop():
    """Proxy to NVD microservice to stop the consumer"""
    try:
        nvd_service_url = os.getenv("NVD_SERVICE_URL", "http://nvd-service:8002")
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(f"{nvd_service_url}/api/v1/consumer/stop")
            return response.json()
    except Exception as e:
        logger.error("Error proxying to NVD service (consumer/stop): %s", str(e))
        raise HTTPException(status_code=503, detail="NVD service unavailable") from e

@router.post("/nvd/queue/consumer/start")
async def proxy_nvd_queue_consumer_start():
    """Alias para iniciar el consumidor de la cola NVD (compatibilidad frontend)"""
    try:
        nvd_service_url = os.getenv("NVD_SERVICE_URL", "http://nvd-service:8002")
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(f"{nvd_service_url}/api/v1/consumer/start")
            return response.json()
    except Exception as e:
        logger.error("Error proxying to NVD service (queue/consumer/start): %s", str(e))
        raise HTTPException(status_code=503, detail="NVD service unavailable") from e

@router.post("/nvd/queue/consumer/stop")
async def proxy_nvd_queue_consumer_stop():
    """Alias para detener el consumidor de la cola NVD (compatibilidad frontend)"""
    try:
        nvd_service_url = os.getenv("NVD_SERVICE_URL", "http://nvd-service:8002")
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(f"{nvd_service_url}/api/v1/consumer/stop")
            return response.json()
    except Exception as e:
        logger.error("Error proxying to NVD service (queue/consumer/stop): %s", str(e))
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

@router.get("/nvd/results/mongodb")
async def get_nvd_results_from_mongodb():
    """Obtener todos los resultados guardados en MongoDB cveScanner.jobs"""
    try:
        from ..database.mongodb_connection import MongoDBConnection
        
        # Conectar a MongoDB
        mongodb = MongoDBConnection()
        await mongodb.connect()
        
        # Consultar todos los trabajos guardados
        cursor = mongodb.db.jobs.find({}).sort("processed_at", -1)
        results = []
        
        async for doc in cursor:
            # Convertir ObjectId a string para serialización JSON
            doc["_id"] = str(doc["_id"])
            
            # Convertir datetime a timestamp para compatibilidad
            if "processed_at" in doc and isinstance(doc["processed_at"], datetime):
                doc["processed_at"] = doc["processed_at"].timestamp()
            
            results.append(doc)
        
        await mongodb.disconnect()
        
        return {
            "success": True,
            "total_jobs": len(results),
            "source": "mongodb_cveScanner_jobs",
            "jobs": results
        }
        
    except Exception as e:
        logger.error(f"Error consultando MongoDB: {e}")
        return {
            "success": False,
            "error": str(e),
            "total_jobs": 0,
            "jobs": []
        }
