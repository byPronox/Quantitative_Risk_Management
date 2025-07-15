"""
ML Prediction Service implementing Strategy and Singleton patterns.
"""
import threading
import logging
from typing import Any, Dict
from abc import ABCMeta

from interfaces.prediction_strategy import PredictionStrategy
from config.settings import settings

logger = logging.getLogger(__name__)

class SingletonMeta(ABCMeta):
    """Metaclass that implements Singleton pattern for model strategies."""
    _instances = {}
    _lock: threading.Lock = threading.Lock()
    
    def __call__(cls, *args, **kwargs):
        with cls._lock:
            if cls not in cls._instances:
                cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]

class CICIDSPredictionStrategy(PredictionStrategy, metaclass=SingletonMeta):
    """CICIDS model prediction strategy with singleton pattern."""
    
    def __init__(self):
        import joblib
        try:
            self.model = joblib.load(settings.CICIDS_MODEL_PATH)
            logger.info("Loaded CICIDS model from %s", settings.CICIDS_MODEL_PATH)
        except Exception as e:
            logger.error("Failed to load CICIDS model: %s", e)
            raise
    
    def predict(self, features: Dict[str, Any]) -> float:
        """
        Predict using CICIDS model.
        
        Args:
            features: Dictionary with network traffic features
            
        Returns:
            float: Attack probability (0.0 to 1.0)
        """
        try:
            X = [list(features.values())]
            prediction = self.model.predict_proba(X)[0][1]
            logger.debug("CICIDS prediction: %f for features: %s", prediction, features)
            return float(prediction)
        except Exception as e:
            logger.error("CICIDS prediction failed: %s", e)
            raise
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get CICIDS model information."""
        return {
            "name": "CICIDS",
            "type": "Random Forest Classifier",
            "path": settings.CICIDS_MODEL_PATH,
            "features": "Network traffic features"
        }

class LANLPredictionStrategy(PredictionStrategy, metaclass=SingletonMeta):
    """LANL model prediction strategy with singleton pattern."""
    
    def __init__(self):
        import joblib
        try:
            bundle = joblib.load(settings.LANL_MODEL_PATH)
            self.model = bundle["model"]
            self.user_encoder = bundle["user_encoder"]
            self.computer_encoder = bundle["computer_encoder"]
            logger.info("Loaded LANL model from %s", settings.LANL_MODEL_PATH)
        except Exception as e:
            logger.error("Failed to load LANL model: %s", e)
            raise
    
    def preprocess(self, features: Dict[str, Any]):
        """Preprocess features for LANL model."""
        timestamp = int(features["time"])
        user = features["user"]
        computer = features["computer"]
        
        user_encoded = self.user_encoder.transform([user])[0]
        computer_encoded = self.computer_encoder.transform([computer])[0]
        
        return [[timestamp, user_encoded, computer_encoded]]
    
    def predict(self, features: Dict[str, Any]) -> float:
        """
        Predict using LANL model.
        
        Args:
            features: Dictionary with user activity features (time, user, computer)
            
        Returns:
            float: Anomaly probability (0.0 for normal, 1.0 for anomaly)
        """
        try:
            X = self.preprocess(features)
            prediction = self.model.predict(X)[0]
            # Isolation Forest returns -1 for anomaly, 1 for normal
            result = 1.0 if prediction == -1 else 0.0
            logger.debug("LANL prediction: %f for features: %s", result, features)
            return result
        except Exception as e:
            logger.error("LANL prediction failed: %s", e)
            raise
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get LANL model information."""
        return {
            "name": "LANL",
            "type": "Isolation Forest",
            "path": settings.LANL_MODEL_PATH,
            "features": "User activity features (time, user, computer)"
        }

class PredictionFactory:
    """Factory for creating prediction strategies."""
    
    @staticmethod
    def get_strategy(model_name: str) -> PredictionStrategy:
        """
        Get prediction strategy by model name.
        
        Args:
            model_name: Name of the model ('cicids' or 'lanl')
            
        Returns:
            PredictionStrategy: Concrete strategy instance
            
        Raises:
            ValueError: If model name is not supported
        """
        if model_name.lower() == "cicids":
            return CICIDSPredictionStrategy()
        elif model_name.lower() == "lanl":
            return LANLPredictionStrategy()
        else:
            raise ValueError(f"Unknown model name: {model_name}")
    
    @staticmethod
    def get_available_models():
        """Get list of available models."""
        return ["cicids", "lanl"]
