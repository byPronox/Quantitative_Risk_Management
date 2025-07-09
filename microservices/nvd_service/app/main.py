from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os

from app.api.routes import router


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    app = FastAPI(
        title="NVD Vulnerability Service",
        description="Microservice for NVD vulnerability data and risk analysis",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include API routes
    app.include_router(router, prefix="/api/v1")
    
    @app.get("/")
    async def root():
        return {
            "service": "NVD Vulnerability Service",
            "version": "1.0.0",
            "status": "running",
            "docs": "/docs"
        }
    
    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8002))
    host = os.getenv("HOST", "0.0.0.0")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=os.getenv("ENVIRONMENT", "production") == "development"
    )
