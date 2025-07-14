import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Service configuration
    SERVICE_NAME: str = "report-service"
    SERVICE_VERSION: str = "1.0.0"
    
    # MongoDB configuration
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb+srv://ADMIN:ADMIN@cluster0.7ixig65.mongodb.net/")
    MONGODB_DATABASE: str = os.getenv("MONGODB_DATABASE", "risk_management")
    
    # External services
    BACKEND_SERVICE_URL: str = os.getenv("BACKEND_SERVICE_URL", "http://backend:8000")
    NVD_SERVICE_URL: str = os.getenv("NVD_SERVICE_URL", "http://nvd-service:8002")
    
    # Report generation settings
    REPORTS_TEMP_DIR: str = "/tmp/reports"
    MAX_VULNERABILITIES_PER_REPORT: int = 1000
    
    class Config:
        env_file = ".env"

settings = Settings()
