"""
NVD Service Main Application (Refactored)
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import controllers
from .controllers.nvd_controller import router as nvd_router
from .config.settings import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="NVD Microservice",
    description="National Vulnerability Database microservice for vulnerability analysis",
    version=settings.SERVICE_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(nvd_router, prefix="/api/v1", tags=["NVD Service"])

# Startup event to initialize consumer
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    try:
        logger.info("Starting NVD service...")
        # Import the already initialized queue service from controller
        from .controllers.nvd_controller import queue_service
        consumer_result = queue_service.start_consumer()
        logger.info("Queue consumer startup result: %s", consumer_result)
    except Exception as e:
        logger.warning("Failed to start queue consumer on startup: %s", str(e))

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": settings.SERVICE_NAME,
        "version": settings.SERVICE_VERSION,
        "status": "healthy",
        "environment": settings.ENVIRONMENT
    }

# Health check endpoint
@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": settings.SERVICE_NAME,
        "version": settings.SERVICE_VERSION
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.ENVIRONMENT == "development"
    )
