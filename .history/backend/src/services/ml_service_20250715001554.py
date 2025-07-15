"""
ML Microservice communication service
"""
import logging
from typing import Dict, Any
import httpx

from ..config.settings import settings

logger = logging.getLogger(__name__)


class MLServiceError(Exception):
    """Custom exception for ML service errors"""


class MLServiceUnavailableError(MLServiceError):
    """Exception raised when ML service is unavailable"""


class MLServiceRequestError(MLServiceError):
    """Exception raised for ML service request errors"""


class MLService:
    """Service for communicating with ML prediction microservice"""
    
    def __init__(self):
        self.base_url = settings.ML_SERVICE_URL
        self.timeout = 30.0
    
    async def predict_combined(self, prediction_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send combined prediction request to ML microservice
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/predict/combined/",
                    json=prediction_data
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error("ML microservice error: %s - %s", response.status_code, response.text)
                    raise MLServiceRequestError(f"ML microservice error: {response.status_code}")
                    
        except httpx.RequestError as e:
            logger.error("Failed to connect to ML microservice: %s", str(e))
            raise MLServiceUnavailableError("ML microservice unavailable") from e
        except MLServiceError:
            raise
        except Exception as e:
            logger.error("ML prediction failed: %s", str(e))
            raise MLServiceError(f"ML prediction failed: {str(e)}") from e
    
    async def predict_single(self, prediction_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send single prediction request to ML microservice
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/predict/",
                    json=prediction_data
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error("ML microservice error: %s - %s", response.status_code, response.text)
                    raise MLServiceRequestError(f"ML microservice error: {response.status_code}")
                    
        except httpx.RequestError as e:
            logger.error("Failed to connect to ML microservice: %s", str(e))
            raise MLServiceUnavailableError("ML microservice unavailable") from e
        except MLServiceError:
            raise
        except Exception as e:
            logger.error("ML prediction failed: %s", str(e))
            raise MLServiceError(f"ML prediction failed: {str(e)}") from e
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check health of ML microservice
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/health")
                
                if response.status_code == 200:
                    return {
                        "status": "healthy",
                        "service_response": response.json(),
                        "service_url": self.base_url
                    }
                else:
                    return {
                        "status": "unhealthy",
                        "status_code": response.status_code,
                        "service_url": self.base_url
                    }
                    
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            logger.error("ML microservice health check failed: %s", str(e))
            return {
                "status": "unhealthy",
                "error": str(e),
                "service_url": self.base_url
            }
    
    async def get_service_info(self) -> Dict[str, Any]:
        """
        Get information about the ML microservice
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Try to get service info endpoint
                response = await client.get(f"{self.base_url}/info")
                
                if response.status_code == 200:
                    return response.json()
                else:
                    # Fallback to basic info
                    return {
                        "service": "ML Prediction Service",
                        "url": self.base_url,
                        "status": "running",
                        "endpoints": [
                            "/predict/combined/",
                            "/predict/",
                            "/health"
                        ]
                    }
                    
        except Exception as e:
            logger.error("Failed to get ML service info: %s", str(e))
            return {
                "service": "ML Prediction Service",
                "url": self.base_url,
                "status": "unknown",
                "error": str(e)
            }
