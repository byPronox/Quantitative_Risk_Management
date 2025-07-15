"""
ML Prediction Service Configuration
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
    """ML Prediction Service Settings"""
    
    # Service configuration
    SERVICE_NAME: str = os.getenv("SERVICE_NAME", "ml-prediction-service")
    SERVICE_VERSION: str = os.getenv("SERVICE_VERSION", "1.0.0")
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8001"))
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # Model Configuration
    CICIDS_MODEL_PATH: Optional[str] = os.getenv("CICIDS_MODEL_PATH")
    LANL_MODEL_PATH: Optional[str] = os.getenv("LANL_MODEL_PATH")
    MODELS_BASE_PATH: str = os.getenv("MODELS_BASE_PATH", "/app/models")
    
    # API Configuration
    API_TITLE: str = os.getenv("API_TITLE", "ML Prediction Service")
    API_DESCRIPTION: str = os.getenv("API_DESCRIPTION", "Microservice for machine learning risk predictions using CICIDS and LANL models")
    
    # CORS Configuration
    ALLOWED_ORIGINS: list = os.getenv("ALLOWED_ORIGINS", "*").split(",")
    ALLOWED_METHODS: list = os.getenv("ALLOWED_METHODS", "GET,POST,PUT,DELETE").split(",")
    ALLOWED_HEADERS: list = os.getenv("ALLOWED_HEADERS", "*").split(",")
    
    # Logging Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    
    # Processing Configuration
    MAX_PREDICTION_RETRIES: int = int(os.getenv("MAX_PREDICTION_RETRIES", "3"))
    PREDICTION_TIMEOUT: int = int(os.getenv("PREDICTION_TIMEOUT", "30"))
    
    def __init__(self):
        # Set default model paths if not provided
        if not self.CICIDS_MODEL_PATH:
            # Try Docker path first, then local development path
            docker_path = f"{self.MODELS_BASE_PATH}/rf_cicids2017_model.pkl"
            local_path = str(Path(__file__).parent.parent.parent / "models" / "rf_cicids2017_model.pkl")
            
            if Path(docker_path).exists():
                self.CICIDS_MODEL_PATH = docker_path
            elif Path(local_path).exists():
                self.CICIDS_MODEL_PATH = local_path
            else:
                self.CICIDS_MODEL_PATH = docker_path  # Default to docker path
        
        if not self.LANL_MODEL_PATH:
            # Try Docker path first, then local development path
            docker_path = f"{self.MODELS_BASE_PATH}/isolation_forest_model.pkl"
            local_path = str(Path(__file__).parent.parent.parent / "models" / "isolation_forest_model.pkl")
            
            if Path(docker_path).exists():
                self.LANL_MODEL_PATH = docker_path
            elif Path(local_path).exists():
                self.LANL_MODEL_PATH = local_path
            else:
                self.LANL_MODEL_PATH = docker_path  # Default to docker path


# Global settings instance
settings = Settings()
