from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router as reports_router
from app.database import MongoDBConnection
from app.config import settings
import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Report Generation Service",
    description="Microservice for generating vulnerability assessment reports",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(reports_router)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Report Generation Service",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "generate_report": "/api/reports/generate",
            "download_report": "/api/reports/{report_id}/download",
            "preview_report": "/api/reports/{report_id}/preview",
            "report_types": "/api/reports/types"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check MongoDB connection
        db = MongoDBConnection.get_database()
        if db is not None:
            mongodb_status = "connected"
        else:
            mongodb_status = "disconnected"
    except Exception as e:
        mongodb_status = f"error: {str(e)}"
    
    return {
        "status": "healthy",
        "service": settings.SERVICE_NAME,
        "version": settings.SERVICE_VERSION,
        "mongodb": mongodb_status,
        "temp_dir": settings.REPORTS_TEMP_DIR
    }

@app.on_event("startup")
async def startup_event():
    """Initialize connections and setup on startup"""
    logger.info(f"Starting {settings.SERVICE_NAME} v{settings.SERVICE_VERSION}")
    
    # Create reports temp directory
    os.makedirs(settings.REPORTS_TEMP_DIR, exist_ok=True)
    logger.info(f"Reports temp directory: {settings.REPORTS_TEMP_DIR}")
    
    # Connect to MongoDB
    try:
        await MongoDBConnection.connect()
        logger.info("MongoDB connection established")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        # Continue without MongoDB - service can generate reports from local data

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info(f"Shutting down {settings.SERVICE_NAME}")
    
    # Close MongoDB connection
    try:
        await MongoDBConnection.disconnect()
        logger.info("MongoDB connection closed")
    except Exception as e:
        logger.error(f"Error closing MongoDB connection: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
