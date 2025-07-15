"""
Main application entry point for Risk Management API Gateway
"""
import sys
import os
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent
sys.path.insert(0, str(src_path))

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from config.settings import settings
from config.database import init_db
from controllers.health_controller import router as health_router
from controllers.risk_controller import router as risk_router
from controllers.nvd_controller import router as nvd_router
from controllers.ml_proxy_controller import router as ml_proxy_router
from controllers.nvd_proxy_controller import router as nvd_proxy_router
from controllers.gateway_controller import router as gateway_router
from middleware.error_handler import ErrorHandlerMiddleware
from middleware.logging_middleware import LoggingMiddleware

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    
    app = FastAPI(
        title="Risk Management API Gateway",
        description="API Gateway for Quantitative Risk Management",
        version=settings.API_VERSION,
        docs_url=f"/api/{settings.API_VERSION}/docs",
        redoc_url=f"/api/{settings.API_VERSION}/redoc",
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure properly for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add custom middleware
    app.add_middleware(ErrorHandlerMiddleware)
    app.add_middleware(LoggingMiddleware)
    
    # Include routers
    app.include_router(health_router, prefix=f"/api/{settings.API_VERSION}", tags=["Health"])
    app.include_router(risk_router, prefix=f"/api/{settings.API_VERSION}", tags=["Risk Analysis"])
    app.include_router(nvd_router, prefix=f"/api/{settings.API_VERSION}", tags=["NVD"])
    app.include_router(ml_proxy_router, prefix=f"/api/{settings.API_VERSION}", tags=["ML Predictions"])
    app.include_router(nvd_proxy_router, prefix=f"/api/{settings.API_VERSION}", tags=["NVD Proxy"])
    
    # Compatibility routes (without API prefix for existing frontend)
    app.include_router(risk_router, tags=["Compatibility"])
    app.include_router(ml_proxy_router, tags=["ML Compatibility"])
    app.include_router(nvd_proxy_router, tags=["NVD Compatibility"])
    
    @app.on_event("startup")
    async def startup_event():
        """Initialize application on startup"""
        logger.info("Starting Risk Management API Gateway")
        await init_db()
        logger.info("Application startup completed")
    
    @app.on_event("shutdown")
    async def shutdown_event():
        """Cleanup on application shutdown"""
        logger.info("Shutting down Risk Management API Gateway")
    
    return app


app = create_app()

if __name__ == "__main__":
    uvicorn.run(
        app,  # Pass the app object directly, not as string
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=False,  # Set to False for production
        log_level=settings.LOG_LEVEL.lower()
    )
