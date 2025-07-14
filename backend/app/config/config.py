# backend/app/config.py
"""
Centralized configuration for secrets, model paths, and environment variables.
All sensitive data should be loaded from environment variables or Docker secrets.
"""
import os

class Settings:
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/postgres")
    
    # MongoDB Atlas
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb+srv://ADMIN:ADMIN@cluster0.7ixig65.mongodb.net/")
    MONGODB_DATABASE: str = os.getenv("MONGODB_DATABASE", "quantitative_risk_management")
    
    # NVD API
    NVD_API_KEY: str = os.getenv("NVD_API_KEY", "")
    # Model paths (corregido para apuntar a /app/ml/)
    CICIDS_MODEL_PATH: str = os.getenv("CICIDS_MODEL_PATH", "/app/ml/rf_cicids2017_model.pkl")
    LANL_MODEL_PATH: str = os.getenv("LANL_MODEL_PATH", "/app/ml/isolation_forest_model.pkl")
    # Message queue (example: Azure Service Bus connection string)
    QUEUE_CONNECTION_STRING: str = os.getenv("QUEUE_CONNECTION_STRING", "")
    QUEUE_NAME: str = os.getenv("QUEUE_NAME", "risk-tasks")
    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379/0")
    
    # Services URLs
    NVD_SERVICE_URL: str = os.getenv("NVD_SERVICE_URL", "http://nvd-service:8002")

settings = Settings()
