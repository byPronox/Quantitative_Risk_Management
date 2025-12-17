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
from config.database import init_db, SessionLocal
from controllers.risk_controller import router as risk_router
from controllers.gateway_controller import router as gateway_router
from controllers.nmap_controller import router as nmap_router
from controllers.nmap_gateway_controller import router as nmap_gateway_router
from controllers.enhanced_risk_controller import router as enhanced_risk_router
from controllers.health_controller import router as health_router
from controllers.auth_controller import router as auth_router, seed_default_user
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
        allow_headers=["*", "ngrok-skip-browser-warning"],  # Allow ngrok header to skip browser warning
    )
    
    # Add custom middleware
    app.add_middleware(ErrorHandlerMiddleware)
    app.add_middleware(LoggingMiddleware)
    
    # Include routers
    app.include_router(auth_router, prefix=f"/api/{settings.API_VERSION}", tags=["Authentication"])
    app.include_router(health_router, prefix=f"/api/{settings.API_VERSION}", tags=["Health"])
    app.include_router(risk_router, prefix=f"/api/{settings.API_VERSION}", tags=["Risk Analysis"])
    app.include_router(gateway_router, prefix=f"/api/{settings.API_VERSION}", tags=["Gateway"])
    app.include_router(nmap_router, prefix=f"/api/{settings.API_VERSION}", tags=["Nmap Scanner"])
    app.include_router(nmap_gateway_router, prefix=f"/api/{settings.API_VERSION}", tags=["Nmap Gateway"])
    app.include_router(enhanced_risk_router, prefix=f"/api/{settings.API_VERSION}", tags=["Enhanced Risk Analysis"])
    
    # Compatibility routes (without API prefix for existing frontend)
    app.include_router(auth_router, tags=["Auth Compatibility"])
    app.include_router(health_router, tags=["Health Compatibility"])
    app.include_router(risk_router, tags=["Compatibility"])
    app.include_router(gateway_router, tags=["Gateway Compatibility"])
    app.include_router(nmap_router, tags=["Nmap Compatibility"])
    app.include_router(nmap_gateway_router, tags=["Nmap Gateway Compatibility"])
    app.include_router(enhanced_risk_router, tags=["Enhanced Risk Compatibility"])
    
    @app.on_event("startup")
    async def startup_event():
        """Initialize application on startup"""
        logger.info("Starting Risk Management API Gateway")
        await init_db()
        
        # Seed default user (qrms/qrms)
        try:
            db = SessionLocal()
            seed_default_user(db)
            db.close()
        except Exception as e:
            logger.warning(f"Could not seed default user: {e}")
        
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
