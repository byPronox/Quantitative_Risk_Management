# backend/app/middleware/kong_middleware.py
"""
Kong Gateway integration middleware
"""
import logging
import httpx
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from config.kong_config import kong_settings

logger = logging.getLogger("kong_middleware")

class KongIntegrationMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle Kong Gateway integration and service registration
    """
    
    async def dispatch(self, request: Request, call_next):
        # Add Kong-specific headers if needed
        request.headers.__dict__["_list"].append(
            (b"x-service-name", kong_settings.BACKEND_SERVICE_NAME.encode())
        )
        
        # Process the request
        response = await call_next(request)
        
        # Add Kong-specific response headers
        response.headers["X-Kong-Service"] = kong_settings.BACKEND_SERVICE_NAME
        response.headers["X-Kong-Proxy"] = kong_settings.KONG_PROXY_URL
        
        return response

class KongServiceRegistration:
    """
    Helper class to register services with Kong Gateway
    """
    
    def __init__(self):
        self.headers = {
            "Authorization": f"Bearer {kong_settings.KONG_TOKEN}",
            "Content-Type": "application/json"
        }
    
    async def register_service(self):
        """Register the backend service with Kong"""
        if not kong_settings.KONG_TOKEN:
            logger.warning("Kong token not provided, skipping service registration")
            return
        
        # Register Backend Service
        await self._register_backend_service()
        
        # Register NVD API Service (as proxy)
        await self._register_nvd_api_service()
    
    async def _register_backend_service(self):
        """Register the main backend service"""
        service_config = {
            "name": kong_settings.BACKEND_SERVICE_NAME,
            "url": kong_settings.BACKEND_SERVICE_URL,
            "protocol": "http",
            "host": "backend",
            "port": 8000,
            "path": "/",
            "tags": ["quantitative-risk", "backend"]
        }
        
        try:
            async with httpx.AsyncClient() as client:
                # Register or update service
                response = await client.put(
                    f"{kong_settings.KONG_ADMIN_API}/services/{kong_settings.BACKEND_SERVICE_NAME}",
                    headers=self.headers,
                    json=service_config
                )
                
                if response.status_code in [200, 201]:
                    logger.info(f"Service {kong_settings.BACKEND_SERVICE_NAME} registered successfully with Kong")
                    await self._create_routes()
                else:
                    logger.error(f"Failed to register service with Kong: {response.status_code} - {response.text}")
        
        except Exception as e:
            logger.error(f"Error registering service with Kong: {e}")
    
    async def _register_nvd_api_service(self):
        """Register NVD API as a proxied service through Kong"""
        nvd_service_config = {
            "name": "nvd-api-service",
            "url": "https://services.nvd.nist.gov/rest/json",
            "protocol": "https",
            "host": "services.nvd.nist.gov",
            "port": 443,
            "path": "/rest/json",
            "tags": ["nvd", "security", "vulnerabilities"]
        }
        
        try:
            async with httpx.AsyncClient() as client:
                # Register NVD API service
                response = await client.put(
                    f"{kong_settings.KONG_ADMIN_API}/services/nvd-api-service",
                    headers=self.headers,
                    json=nvd_service_config
                )
                
                if response.status_code in [200, 201]:
                    logger.info("NVD API service registered successfully with Kong")
                    await self._create_nvd_api_routes()
                    await self._configure_nvd_api_key()
                else:
                    logger.error(f"Failed to register NVD API service: {response.status_code} - {response.text}")
        
        except Exception as e:
            logger.error(f"Error registering NVD API service with Kong: {e}")
    
    async def _create_nvd_api_routes(self):
        """Create routes for NVD API service"""
        nvd_route_config = {
            "name": "nvd-api-route",
            "service": {"name": "nvd-api-service"},
            "paths": ["/nvd-api/~"],
            "methods": ["GET", "POST"],
            "strip_path": True
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{kong_settings.KONG_ADMIN_API}/routes",
                    headers=self.headers,
                    json=nvd_route_config
                )
                
                if response.status_code in [200, 201]:
                    logger.info("NVD API route created successfully")
                    route_data = response.json()
                    route_id = route_data.get("id")
                    if route_id:
                        await self._configure_cors_plugin(route_id)
                else:
                    logger.warning(f"NVD API route creation response: {response.status_code} - {response.text}")
        
        except Exception as e:
            logger.error(f"Error creating NVD API route: {e}")
    
    async def register_microservices(self):
        """Register all microservices with Kong"""
        if not kong_settings.KONG_TOKEN:
            logger.warning("Kong token not provided, skipping microservice registration")
            return
        
        # Microservices to register
        microservices = [
            {
                "name": "ml-prediction-service",
                "url": "http://ml-prediction-service:8001",
                "routes": [
                    {"path": "/ml", "strip_path": True}
                ]
            },
            {
                "name": "nvd-service", 
                "url": "http://nvd-service:8002",
                "routes": [
                    {"path": "/nvd", "strip_path": True}
                ]
            }
        ]
        
        for service in microservices:
            try:
                await self._register_service(service["name"], service["url"])
                
                # Register routes for the service
                for route in service["routes"]:
                    await self._register_route(service["name"], route["path"], route.get("strip_path", True))
                    
                logger.info(f"Successfully registered microservice: {service['name']}")
                
            except Exception as e:
                logger.error(f"Failed to register microservice {service['name']}: {e}")
                
        # Register API key plugin for NVD service
        await self._configure_nvd_api_key()
        
        # Configure CORS for all services
        await self._configure_cors()
    
    async def _register_service(self, service_name: str, service_url: str):
        """Register a single service with Kong"""
        service_data = {
            "name": service_name,
            "url": service_url,
            "protocol": "http",
            "connect_timeout": 30000,
            "write_timeout": 30000,
            "read_timeout": 30000
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Check if service exists
            try:
                response = await client.get(
                    f"{kong_settings.KONG_ADMIN_API}/services/{service_name}",
                    headers=self.headers
                )
                if response.status_code == 200:
                    # Update existing service
                    response = await client.patch(
                        f"{kong_settings.KONG_ADMIN_API}/services/{service_name}",
                        headers=self.headers,
                        json=service_data
                    )
                    logger.info(f"Updated existing Kong service: {service_name}")
                else:
                    # Create new service
                    response = await client.post(
                        f"{kong_settings.KONG_ADMIN_API}/services",
                        headers=self.headers,
                        json=service_data
                    )
                    logger.info(f"Created new Kong service: {service_name}")
                    
            except Exception as e:
                # Create new service if check failed
                response = await client.post(
                    f"{kong_settings.KONG_ADMIN_API}/services",
                    headers=self.headers,
                    json=service_data
                )
                logger.info(f"Created new Kong service: {service_name}")
    
    async def _register_route(self, service_name: str, path: str, strip_path: bool = True):
        """Register a route for a service"""
        route_data = {
            "name": f"{service_name}-route",
            "paths": [path],
            "strip_path": strip_path,
            "preserve_host": False
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                # Check if route exists
                response = await client.get(
                    f"{kong_settings.KONG_ADMIN_API}/services/{service_name}/routes",
                    headers=self.headers
                )
                
                routes = response.json().get("data", [])
                existing_route = next((r for r in routes if path in r.get("paths", [])), None)
                
                if existing_route:
                    # Update existing route
                    response = await client.patch(
                        f"{kong_settings.KONG_ADMIN_API}/routes/{existing_route['id']}",
                        headers=self.headers,
                        json=route_data
                    )
                    logger.info(f"Updated route {path} for service {service_name}")
                else:
                    # Create new route
                    response = await client.post(
                        f"{kong_settings.KONG_ADMIN_API}/services/{service_name}/routes",
                        headers=self.headers,
                        json=route_data
                    )
                    logger.info(f"Created route {path} for service {service_name}")
                    
            except Exception as e:
                logger.error(f"Failed to register route {path} for {service_name}: {e}")
    
    async def _configure_nvd_api_key(self):
        """Configure API key plugin for NVD service"""
        try:
            # Configure request-transformer plugin to add NVD API key
            plugin_data = {
                "name": "request-transformer",
                "config": {
                    "add": {
                        "headers": [f"apiKey:{kong_settings.NVD_API_KEY}"] if kong_settings.NVD_API_KEY else []
                    }
                }
            }
            
            if kong_settings.NVD_API_KEY:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        f"{kong_settings.KONG_ADMIN_API}/services/nvd-service/plugins",
                        headers=self.headers,
                        json=plugin_data
                    )
                    logger.info("Configured NVD API key plugin")
                    
        except Exception as e:
            logger.warning(f"Failed to configure NVD API key plugin: {e}")
    
    async def _configure_cors(self):
        """Configure CORS plugin for all services"""
        try:
            cors_config = {
                "name": "cors",
                "config": {
                    "origins": ["*"],
                    "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                    "headers": ["Accept", "Accept-Version", "Content-Length", "Content-MD5", "Content-Type", "Date", "X-Auth-Token"],
                    "exposed_headers": ["X-Auth-Token"],
                    "credentials": True,
                    "max_age": 3600
                }
            }
            
            # Apply CORS to both microservices
            services = ["ml-prediction-service", "nvd-service"]
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                for service in services:
                    try:
                        response = await client.post(
                            f"{kong_settings.KONG_ADMIN_API}/services/{service}/plugins",
                            headers=self.headers,
                            json=cors_config
                        )
                        logger.info(f"Configured CORS for {service}")
                    except Exception as e:
                        logger.warning(f"Failed to configure CORS for {service}: {e}")
                        
        except Exception as e:
            logger.warning(f"Failed to configure CORS: {e}")

class MongoDBAutoSaveMiddleware(BaseHTTPMiddleware):
    """
    Middleware to automatically save NVD results to MongoDB when accessing /nvd/results/all
    """
    
    async def dispatch(self, request: Request, call_next):
        # Check if this is the specific endpoint we want to intercept
        if request.url.path == "/nvd/results/all" and request.method == "GET":
            logger.info("Intercepting /nvd/results/all request for MongoDB auto-save")
            
            try:
                # Get results from NVD service directly
                nvd_service_url = "http://nvd-service:8002"
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(f"{nvd_service_url}/api/v1/results/all")
                    if response.status_code != 200:
                        logger.error(f"Failed to get results from NVD service: {response.status_code}")
                        # Fall back to normal processing
                        return await call_next(request)
                    
                    results_data = response.json()
                    logger.info(f"Retrieved data from NVD service: {len(results_data.get('jobs', []))} jobs")
                    
                    # Automatically save to MongoDB if there are completed jobs
                    if results_data.get("success") and results_data.get("jobs"):
                        completed_jobs = [job for job in results_data["jobs"] 
                                        if job.get("status") == "completed" and job.get("vulnerabilities")]
                        if completed_jobs:
                            logger.info(f"Auto-saving {len(completed_jobs)} completed jobs to MongoDB")
                            await self._save_to_mongodb(completed_jobs)
                    
                    # Return the results as JSON response with CORS headers
                    response = JSONResponse(content=results_data)
                    # Add CORS headers manually
                    response.headers["Access-Control-Allow-Origin"] = "*"
                    response.headers["Access-Control-Allow-Credentials"] = "true"
                    response.headers["Access-Control-Allow-Methods"] = "*"
                    response.headers["Access-Control-Allow-Headers"] = "*"
                    return response
                    
            except Exception as e:
                logger.error(f"Error in MongoDB auto-save middleware: {e}")
                # Fall back to normal processing if anything goes wrong
                return await call_next(request)
        
        # For all other requests, proceed normally
        return await call_next(request)
    
    async def _save_to_mongodb(self, jobs_data):
        """Save jobs to MongoDB"""
        try:
            from database.mongodb import MongoDBConnection
            import time
            from datetime import datetime
            
            mongodb = MongoDBConnection()
            await mongodb.connect()
            logger.info("MongoDB connection established for auto-save")
            
            for job in jobs_data:
                if job.get("status") == "completed" and job.get("vulnerabilities"):
                    # Check if job already exists
                    existing_job = await mongodb.db.jobs.find_one({"job_id": job.get("job_id")})
                    if existing_job:
                        logger.info(f"Job {job.get('job_id')} already exists in MongoDB, skipping")
                        continue
                    
                    logger.info(f"Auto-saving job {job.get('job_id')} with {len(job.get('vulnerabilities', []))} vulnerabilities")
                    
                    # Process vulnerabilities to fix date format issues
                    processed_vulnerabilities = []
                    for vuln in job.get("vulnerabilities", []):
                        processed_vuln = vuln.copy()
                        
                        # Fix date fields in CVE data
                        if "cve" in processed_vuln and processed_vuln["cve"]:
                            cve_data = processed_vuln["cve"].copy()
                            
                            # Convert string dates to datetime objects
                            if "published" in cve_data and isinstance(cve_data["published"], str):
                                try:
                                    cve_data["published"] = datetime.fromisoformat(cve_data["published"].replace('Z', '+00:00'))
                                except:
                                    cve_data["published"] = datetime.now()
                            
                            if "lastModified" in cve_data and isinstance(cve_data["lastModified"], str):
                                try:
                                    cve_data["lastModified"] = datetime.fromisoformat(cve_data["lastModified"].replace('Z', '+00:00'))
                                except:
                                    cve_data["lastModified"] = datetime.now()
                            
                            processed_vuln["cve"] = cve_data
                        
                        processed_vulnerabilities.append(processed_vuln)
                    
                    job_document = {
                        "job_id": job.get("job_id", ""),
                        "keyword": job.get("keyword", ""),
                        "status": job.get("status", "pending"),
                        "total_results": int(job.get("total_results", 0)),
                        "processed_at": float(job.get("timestamp", time.time())),
                        "processed_via": "auto_save_middleware",
                        "vulnerabilities": processed_vulnerabilities
                    }
                    
                    await mongodb.db.jobs.insert_one(job_document)
                    logger.info(f"Auto-saved job {job.get('job_id')} to MongoDB")
            
            await mongodb.disconnect()
            logger.info("MongoDB auto-save process completed")
            
        except Exception as e:
            logger.error(f"Error in MongoDB auto-save: {e}")
