# backend/app/middleware/cors_middleware.py
"""
CORS middleware configuration for the backend.
"""
from fastapi.middleware.cors import CORSMiddleware

def setup_cors_middleware(app):
    """
    Setup CORS middleware for the FastAPI application.
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, specify exact origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
