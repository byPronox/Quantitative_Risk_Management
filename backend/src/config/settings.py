"""
Application settings and configuration
"""
from pathlib import Path
from typing import Optional
import os

try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_VERSION: str = "v1"
    
    # Database Configuration (PostgreSQL/Supabase)
    DATABASE_URL: str = "sqlite:///./risk_management.db"
    
    # NVD Configuration
    NVD_API_KEY: str = ""
    USE_KONG_NVD: bool = False
    
    # Kong Configuration (loaded from .env)
    KONG_PROXY_URL: Optional[str] = None
    KONG_ADMIN_URL: Optional[str] = None
    KONG_ADMIN_API: Optional[str] = None
    KONG_CONTROL_PLANE_ID: Optional[str] = None
    
    # RabbitMQ Configuration (loaded from .env)
    RABBITMQ_HOST: str = "rabbitmq"
    RABBITMQ_PORT: int = 5672
    RABBITMQ_USER: str = "guest"
    RABBITMQ_PASSWORD: str = "guest"
    RABBITMQ_QUEUE: str = "nvd_analysis_queue"
    RABBITMQ_URL: str = "amqp://guest:guest@rabbitmq:5672/"
    
    # Redis Configuration (loaded from .env)
    REDIS_URL: str = "redis://redis:6379/0"
    
    # Microservices URLs (loaded from .env)
    ML_SERVICE_URL: str = "http://ml-prediction-service:8001"
    NVD_SERVICE_URL: str = "http://nvd-service:8002"
    NMAP_SERVICE_URL: str = "http://nmap-scanner-service:8004"
    REPORT_SERVICE_URL: str = "http://report-service:8003"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # Security (loaded from .env)
    SECRET_KEY: str = "change_this_in_production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Frontend Configuration (loaded from .env)
    VITE_API_URL: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra env vars


# Global settings instance
settings = Settings()
