from fastapi import APIRouter, HTTPException, Request
from typing import Dict, Any
import httpx
import os
import logging
import time
from datetime import datetime
from services.user_service import user_login, get_user_profile
from fastapi import Body

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

@router.get("/nvd/results/mongodb")
async def get_nvd_results_from_mongodb():
    """Obtener todos los resultados guardados en MongoDB cveScanner.jobs"""
    try:
        from database.mongodb import MongoDBConnection
        
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
    logger.info("=== NVD Results All endpoint called ===")
    try:
        nvd_service_url = os.getenv("NVD_SERVICE_URL", "http://nvd-service:8002")
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{nvd_service_url}/api/v1/results/all")
            results_data = response.json()
            
            # Debug logging
            logger.info(f"Results data keys: {list(results_data.keys())}")
            logger.info(f"Success: {results_data.get('success')}, Jobs count: {len(results_data.get('jobs', []))}")
            
            # Guardar automáticamente en MongoDB si hay trabajos completados
            if results_data.get("success") and results_data.get("jobs") and len(results_data.get("jobs", [])) > 0:
                # Filtrar solo trabajos completados con vulnerabilidades
                completed_jobs = [job for job in results_data["jobs"] if job.get("status") == "completed" and job.get("vulnerabilities")]
                logger.info(f"Completed jobs found: {len(completed_jobs)}")
                if completed_jobs:
                    logger.info("Starting MongoDB save process...")
                    await save_results_to_mongodb(completed_jobs)
                else:
                    logger.info("No completed jobs with vulnerabilities found")
            
            return results_data
    except Exception as e:
        logger.error("Error proxying to NVD service (results/all): %s", str(e))
        raise HTTPException(status_code=503, detail="NVD service unavailable") from e

async def save_results_to_mongodb(jobs_data):
    """Guarda los resultados de trabajos NVD en MongoDB con tu estructura"""
    logger.info(f"MongoDB save function called with {len(jobs_data)} jobs")
    try:
        from database.mongodb import MongoDBConnection
        from datetime import datetime
        
        # Conectar a MongoDB
        mongodb = MongoDBConnection()
        await mongodb.connect()
        logger.info("MongoDB connection established in save function")
        
        for job in jobs_data:
            if job.get("status") == "completed" and job.get("vulnerabilities"):
                logger.info(f"Processing job {job.get('job_id')} with {len(job.get('vulnerabilities', []))} vulnerabilities")
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

@router.get("/mongodb/nvd/results/all")
async def get_nvd_results_mongodb_enhanced():
    """Get all NVD results with automatic MongoDB saving (bypasses Kong interception)"""
    logger.info("=== MongoDB-enhanced NVD Results endpoint called ===")
    try:
        nvd_service_url = os.getenv("NVD_SERVICE_URL", "http://nvd-service:8002")
        
        # Fetch results directly from NVD service
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{nvd_service_url}/api/v1/results/all")
            results_data = response.json()
            
            # Debug logging
            logger.info(f"Results data keys: {list(results_data.keys())}")
            logger.info(f"Success: {results_data.get('success')}, Jobs count: {len(results_data.get('jobs', []))}")
            
            # Automatically save to MongoDB if there are completed jobs
            if results_data.get("success") and results_data.get("jobs") and len(results_data.get("jobs", [])) > 0:
                # Filter only completed jobs with vulnerabilities
                completed_jobs = [job for job in results_data["jobs"] if job.get("status") == "completed" and job.get("vulnerabilities")]
                logger.info(f"Completed jobs found: {len(completed_jobs)}")
                if completed_jobs:
                    logger.info("Starting MongoDB save process...")
                    await save_results_to_mongodb(completed_jobs)
                    logger.info("MongoDB save process completed")
                else:
                    logger.info("No completed jobs with vulnerabilities found")
            
            return results_data
            
    except Exception as e:
        logger.error("Error in MongoDB-enhanced NVD results endpoint: %s", str(e))
        raise HTTPException(status_code=503, detail="NVD service unavailable") from e

@router.get("/reports/general/keywords")
async def get_general_reports_by_keywords():
    """Get all vulnerability data grouped by keywords from MongoDB for General Reports"""
    try:
        from database.mongodb import MongoDBConnection
        from datetime import datetime
        
        # Connect to MongoDB
        mongodb = MongoDBConnection()
        await mongodb.connect()
        
        # Get all jobs from MongoDB and group by keyword
        cursor = mongodb.db.jobs.find({}).sort("processed_at", -1)
        jobs_by_keyword = {}
        
        async for job in cursor:
            keyword = job.get("keyword", "Unknown")
            if keyword not in jobs_by_keyword:
                jobs_by_keyword[keyword] = {
                    "keyword": keyword,
                    "total_jobs": 0,
                    "total_vulnerabilities": 0,
                    "latest_analysis": None,
                    "jobs": []
                }
            
            # Convert processed_at to readable format
            processed_at = job.get("processed_at")
            if isinstance(processed_at, (int, float)):
                processed_at_readable = datetime.fromtimestamp(processed_at).strftime("%Y-%m-%d %H:%M:%S")
            else:
                processed_at_readable = str(processed_at)
            
            job_summary = {
                "job_id": job.get("job_id"),
                "status": job.get("status"),
                "total_results": job.get("total_results", 0),
                "vulnerabilities_count": len(job.get("vulnerabilities", [])),
                "processed_at": processed_at_readable,
                "processed_at_timestamp": processed_at
            }
            
            jobs_by_keyword[keyword]["jobs"].append(job_summary)
            jobs_by_keyword[keyword]["total_jobs"] += 1
            jobs_by_keyword[keyword]["total_vulnerabilities"] += job_summary["vulnerabilities_count"]
            
            # Update latest analysis
            if (jobs_by_keyword[keyword]["latest_analysis"] is None or 
                processed_at > jobs_by_keyword[keyword]["latest_analysis"]):
                jobs_by_keyword[keyword]["latest_analysis"] = processed_at_readable
        
        await mongodb.disconnect()
        
        # Convert to list and sort by latest analysis
        keywords_list = list(jobs_by_keyword.values())
        keywords_list.sort(key=lambda x: x["total_vulnerabilities"], reverse=True)
        
        return {
            "success": True,
            "total_keywords": len(keywords_list),
            "keywords": keywords_list
        }
        
    except Exception as e:
        logger.error(f"Error getting general reports by keywords: {e}")
        return {
            "success": False,
            "error": str(e),
            "total_keywords": 0,
            "keywords": []
        }

@router.get("/reports/general/keyword/{keyword}")
async def get_detailed_report_by_keyword(keyword: str):
    """Get detailed vulnerability report for a specific keyword from MongoDB"""
    try:
        from database.mongodb import MongoDBConnection
        from datetime import datetime
        
        # Connect to MongoDB
        mongodb = MongoDBConnection()
        await mongodb.connect()
        
        # Get all jobs for the specific keyword
        cursor = mongodb.db.jobs.find({"keyword": keyword}).sort("processed_at", -1)
        jobs = []
        all_vulnerabilities = []
        total_vulnerabilities = 0
        
        async for job in cursor:
            # Convert ObjectId to string for JSON serialization
            job["_id"] = str(job["_id"])
            
            # Convert processed_at to readable format
            processed_at = job.get("processed_at")
            if isinstance(processed_at, (int, float)):
                job["processed_at_readable"] = datetime.fromtimestamp(processed_at).strftime("%Y-%m-%d %H:%M:%S")
            
            # Add vulnerabilities to the complete list
            vulnerabilities = job.get("vulnerabilities", [])
            all_vulnerabilities.extend(vulnerabilities)
            total_vulnerabilities += len(vulnerabilities)
            
            jobs.append(job)
        
        await mongodb.disconnect()
        
        # Analyze vulnerability severity distribution
        severity_stats = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0, "Unknown": 0}
        cve_years = {}
        
        for vuln in all_vulnerabilities:
            # Count by severity
            metrics = vuln.get("cve", {}).get("metrics", {})
            if "cvssMetricV31" in metrics and metrics["cvssMetricV31"]:
                severity = metrics["cvssMetricV31"][0].get("cvssData", {}).get("baseSeverity", "Unknown")
            elif "cvssMetricV2" in metrics and metrics["cvssMetricV2"]:
                score = metrics["cvssMetricV2"][0].get("cvssData", {}).get("baseScore", 0)
                if score >= 9.0:
                    severity = "Critical"
                elif score >= 7.0:
                    severity = "High"
                elif score >= 4.0:
                    severity = "Medium"
                else:
                    severity = "Low"
            else:
                severity = "Unknown"
            
            severity_stats[severity] = severity_stats.get(severity, 0) + 1
            
            # Count by year
            published = vuln.get("cve", {}).get("published", "")
            if published:
                try:
                    if isinstance(published, str):
                        year = published[:4]
                    else:
                        # If it's a datetime object, extract year
                        year = str(published.year) if hasattr(published, 'year') else str(published)[:4]
                    cve_years[year] = cve_years.get(year, 0) + 1
                except:
                    # If any error, skip this entry
                    pass
        
        return {
            "success": True,
            "keyword": keyword,
            "total_jobs": len(jobs),
            "total_vulnerabilities": total_vulnerabilities,
            "severity_distribution": severity_stats,
            "vulnerabilities_by_year": dict(sorted(cve_years.items(), reverse=True)),
            "jobs": jobs,
            "vulnerabilities": all_vulnerabilities
        }
        
    except Exception as e:
        logger.error(f"Error getting detailed report for keyword {keyword}: {e}")
        return {
            "success": False,
            "error": str(e),
            "keyword": keyword,
            "jobs": [],
            "vulnerabilities": []
        }

@router.post("/user/login")
async def login_user(data: dict = Body(...)):
    """Login user via external microservice (Render)"""
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        raise HTTPException(status_code=400, detail="Username and password required")
    return await user_login(username, password)

@router.get("/user/profile")
async def user_profile(token: str):
    """Get user profile from external microservice (Render)"""
    return await get_user_profile(token)
