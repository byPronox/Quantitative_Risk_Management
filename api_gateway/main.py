# api_gateway/main.py
"""
FastAPI entry point for the API Gateway, using dependency injection and service abstraction.
"""
from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
import logging
from services.http_backend_service import HttpBackendService
from interfaces.backend_service_interface import BackendServiceInterface

app = FastAPI()

# Habilita CORS para permitir preflight y peticiones desde el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # O especifica ["http://localhost:5173"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api_gateway")

# Dependency injection for backend service
async def get_backend_service() -> BackendServiceInterface:
    return HttpBackendService()

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/predict/cicids/")
async def gateway_cicids(request: Request, backend: BackendServiceInterface = Depends(get_backend_service)):
    data = await request.json()
    try:
        return await backend.predict_cicids(data)
    except Exception as e:
        logger.error("Gateway: CICIDS prediction failed: %s", e)
        return {"error": "CICIDS prediction failed."}, 500

@app.post("/predict/lanl/")
async def gateway_lanl(request: Request, backend: BackendServiceInterface = Depends(get_backend_service)):
    data = await request.json()
    try:
        return await backend.predict_lanl(data)
    except Exception as e:
        logger.error("Gateway: LANL prediction failed: %s", e)
        return {"error": "LANL prediction failed."}, 500

@app.get("/nvd")
async def gateway_nvd(request: Request, backend: BackendServiceInterface = Depends(get_backend_service)):
    params = dict(request.query_params)
    try:
        return await backend.get_nvd(params)
    except Exception as e:
        logger.error("Gateway: NVD request failed: %s", e)
        return {"error": "NVD request failed."}, 500

@app.post("/predict/combined/")
async def gateway_combined(request: Request, backend: BackendServiceInterface = Depends(get_backend_service)):
    data = await request.json()
    try:
        return await backend.predict_combined(data)
    except Exception as e:
        logger.error("Gateway: Combined prediction failed: %s", e)
        return {"error": "Combined prediction failed."}, 500

@app.post("/nvd/analyze_risk")
async def gateway_nvd_analyze_risk(backend: BackendServiceInterface = Depends(get_backend_service)):
    try:
        return await backend.analyze_nvd_risk()
    except Exception as e:
        logger.error("Gateway: NVD analyze risk request failed: %s", e)
        return {"error": "NVD analyze risk failed."}, 500

@app.post("/nvd/enterprise_metrics")
async def gateway_nvd_enterprise_metrics(backend: BackendServiceInterface = Depends(get_backend_service)):
    try:
        return await backend.get_nvd_enterprise_metrics()
    except Exception as e:
        logger.error("Gateway: NVD enterprise metrics request failed: %s", e)
        return {"error": "NVD enterprise metrics failed."}, 500

@app.get("/nvd/queue_status")
async def gateway_nvd_queue_status(backend: BackendServiceInterface = Depends(get_backend_service)):
    try:
        return await backend.get_nvd_queue_status()
    except Exception as e:
        logger.error("Gateway: NVD queue status request failed: %s", e)
        return {"error": "NVD queue status failed."}, 500

@app.post("/nvd/clear_queue")
async def gateway_nvd_clear_queue(backend: BackendServiceInterface = Depends(get_backend_service)):
    try:
        return await backend.clear_nvd_queue()
    except Exception as e:
        logger.error("Gateway: NVD clear queue request failed: %s", e)
        return {"error": "NVD clear queue failed."}, 500

@app.post("/nvd/add_to_queue")
async def gateway_nvd_add_to_queue(request: Request, backend: BackendServiceInterface = Depends(get_backend_service)):
    data = await request.json()
    keyword = data.get("keyword")
    if not keyword:
        return {"error": "Keyword is required"}, 400
    try:
        return await backend.add_keyword_to_queue(keyword)
    except Exception as e:
        logger.error("Gateway: Add keyword to queue request failed: %s", e)
        return {"error": "Add keyword to queue failed."}, 500
