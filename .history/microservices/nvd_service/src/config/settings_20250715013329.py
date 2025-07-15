"""
NVD Service Configuration
"""
import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """NVD Service Settings"""
    
    # Service configuration
    SERVICE_NAME: str = "nvd-service"
    SERVICE_VERSION: str = "1.0.0"
    HOST: str = "0.0.0.0"
    PORT: int = 8002
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # NVD API Configuration
    NVD_API_KEY: Optional[str] = os.getenv("NVD_API_KEY", "")
    NVD_BASE_URL: str = "https://services.nvd.nist.gov/rest/json/cves/2.0"
    
    # Kong Gateway Configuration
    KONG_PROXY_URL: Optional[str] = os.getenv("KONG_PROXY_URL", "")
    USE_KONG_NVD: bool = os.getenv("USE_KONG_NVD", "false").lower() == "true"
    
    # MongoDB Atlas Configuration
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb+srv://ADMIN:ADMIN@cluster0.7ixig65.mongodb.net/")
    MONGODB_DATABASE: str = os.getenv("MONGODB_DATABASE", "cveScanner")
    
    # RabbitMQ Configuration
    RABBITMQ_HOST: str = os.getenv("RABBITMQ_HOST", "rabbitmq")
    RABBITMQ_USER: str = os.getenv("RABBITMQ_USER", "guest")
    RABBITMQ_PASSWORD: str = os.getenv("RABBITMQ_PASSWORD", "guest")
    RABBITMQ_QUEUE: str = os.getenv("RABBITMQ_QUEUE", "nvd_analysis_queue")
    RABBITMQ_URL: str = f"amqp://{RABBITMQ_USER}:{RABBITMQ_PASSWORD}@{RABBITMQ_HOST}:5672/"
    
    # External Services
    BACKEND_URL: str = os.getenv("BACKEND_URL", "http://backend:8000")
    
    # Processing Configuration
    MAX_RETRIES: int = 5
    RETRY_DELAY: int = 2
    REQUEST_TIMEOUT: int = 60
    MAX_VULNERABILITIES_PER_REQUEST: int = 1000
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
