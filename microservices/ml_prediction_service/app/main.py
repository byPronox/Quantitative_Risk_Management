"""
ML Prediction Microservice - Main Application.
"""
import sys
import os

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from api.routes import router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

app = FastAPI(
    title="ML Prediction Service",
    description="Microservice for machine learning risk predictions using CICIDS and LANL models",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api/v1")

# Root endpoint
@app.get("/")
def read_root():
    return {
        "service": "ML Prediction Service",
        "version": "1.0.0",
        "status": "running",
        "endpoints": [
            "/api/v1/health",
            "/api/v1/predict/cicids",
            "/api/v1/predict/lanl", 
            "/api/v1/predict/combined"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
