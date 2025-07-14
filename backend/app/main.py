import sys
sys.path.append('/app')

import os
from fastapi import FastAPI
from database.db import Base, engine
from api.routes import router
from api.document_store_routes import router as document_store_router
import logging
import asyncio

# Set environment variables for microservices if not already set
if not os.getenv("ML_SERVICE_URL"):
    os.environ["ML_SERVICE_URL"] = "http://ml-prediction-service:8001"
if not os.getenv("NVD_SERVICE_URL"):
    os.environ["NVD_SERVICE_URL"] = "http://nvd-service:8002"

# Import middleware
from middleware.cors_middleware import setup_cors_middleware
from middleware.logging_middleware import LoggingMiddleware
from middleware.error_handling_middleware import ErrorHandlingMiddleware
from middleware.kong_middleware import KongIntegrationMiddleware, KongServiceRegistration, MongoDBAutoSaveMiddleware

# Import MongoDB connection
from database.mongodb import MongoDBConnection

app = FastAPI(
    title="Risk Management API Gateway", 
    version="1.0.0",
    description="API Gateway for Risk Management Microservices with Kong Integration and MongoDB"
)

# Set up logging for the app
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("risk_gateway")

# Setup middlewares
setup_cors_middleware(app)
app.add_middleware(ErrorHandlingMiddleware)
app.add_middleware(LoggingMiddleware)
app.add_middleware(MongoDBAutoSaveMiddleware)  # Add BEFORE Kong middleware
app.add_middleware(KongIntegrationMiddleware)

@app.get("/")
def read_root():
    return {
        "message": "Risk Management API Gateway", 
        "kong_proxy": "https://kong-b27b67aff4usnspl9.kongcloud.dev",
        "microservices": {
            "ml_prediction": "/api/v1/proxy/ml/",
            "nvd_service": "/api/v1/proxy/nvd/"
        },
        "mongodb": "enabled"
    }

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "risk-management-gateway"}

# Kong service registration and MongoDB connection on startup
@app.on_event("startup")
async def startup_event():
    logger.info("Starting Risk Management API Gateway with Kong Integration and MongoDB")
    
    # Create database tables (for basic data persistence)
    Base.metadata.create_all(bind=engine)
    
    # Initialize MongoDB connection
    try:
        await MongoDBConnection.connect()
        logger.info("MongoDB connection established successfully")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        # Continue without MongoDB - service can still function partially
    
    # Register microservices with Kong Gateway
    kong_registration = KongServiceRegistration()
    try:
        await kong_registration.register_microservices()
        logger.info("Kong Gateway microservice registration completed")
    except Exception as e:
        logger.warning(f"Kong Gateway registration failed (continuing without it): {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup connections on shutdown."""
    logger.info("Shutting down Risk Management API Gateway")
    
    # Close MongoDB connection
    try:
        await MongoDBConnection.disconnect()
        logger.info("MongoDB connection closed")
    except Exception as e:
        logger.error(f"Error closing MongoDB connection: {e}")

# Include routers
app.include_router(router, prefix="/api/v1")  # Versioned API
app.include_router(router)  # Legacy compatibility (no prefix)
app.include_router(document_store_router, prefix="/api/v1")  # DocumentStore routes

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
