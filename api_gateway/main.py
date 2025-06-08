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
