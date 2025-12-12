"""
NVD Service Configuration
"""
import os
from typing import Optional
from pathlib import Path

# Load environment variables from .env file
def load_env_file():
    """Load environment variables from .env file if it exists"""
    env_file = Path(__file__).parent.parent.parent / ".env"
    if env_file.exists():
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    if key and value and key not in os.environ:
                        os.environ[key] = value

# Load .env file before defining settings
load_env_file()


class Settings:
    """NVD Service Settings"""
    
    # Service configuration
    SERVICE_NAME: str = os.getenv("SERVICE_NAME", "nvd-service")
    SERVICE_VERSION: str = os.getenv("SERVICE_VERSION", "1.0.0")
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8002"))
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # NVD API Configuration
    NVD_API_KEY: Optional[str] = os.getenv("NVD_API_KEY")
    NVD_BASE_URL: str = os.getenv("NVD_BASE_URL", "https://services.nvd.nist.gov/rest/json/cves/2.0")
    
    # Kong Gateway Configuration
    KONG_PROXY_URL: Optional[str] = os.getenv("KONG_PROXY_URL")
    USE_KONG_NVD: bool = os.getenv("USE_KONG_NVD", "false").lower() == "true"
    
    # PostgreSQL/Supabase Configuration
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    
    # RabbitMQ Configuration
    RABBITMQ_HOST: str = os.getenv("RABBITMQ_HOST", "rabbitmq")
    RABBITMQ_USER: str = os.getenv("RABBITMQ_USER", "guest")
    RABBITMQ_PASSWORD: str = os.getenv("RABBITMQ_PASSWORD", "guest")
    RABBITMQ_QUEUE: str = os.getenv("RABBITMQ_QUEUE", "nvd_analysis_queue")
    
    # External Services
    BACKEND_URL: str = os.getenv("BACKEND_URL", "http://backend:8000")
    
    # Processing Configuration
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "5"))
    RETRY_DELAY: int = int(os.getenv("RETRY_DELAY", "2"))
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "60"))
    MAX_VULNERABILITIES_PER_REQUEST: int = int(os.getenv("MAX_VULNERABILITIES_PER_REQUEST", "1000"))
    
    def __init__(self):
        # Validate required environment variables
        if not self.DATABASE_URL:
            raise ValueError("DATABASE_URL environment variable is required")
        
        # Compute derived values
        self.RABBITMQ_URL = f"amqp://{self.RABBITMQ_USER}:{self.RABBITMQ_PASSWORD}@{self.RABBITMQ_HOST}:5672/"


# Global settings instance
settings = Settings()
