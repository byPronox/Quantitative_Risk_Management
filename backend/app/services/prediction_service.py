"""
PredictionFactory and concrete strategies for ML prediction (Factory, Strategy, Singleton Patterns).
"""
import threading
import logging
from typing import Any, Dict
from config.config import settings
from interfaces.prediction_strategy import PredictionStrategy
from abc import ABCMeta

logger = logging.getLogger(__name__)

class SingletonMeta(ABCMeta):
    _instances = {}
    _lock: threading.Lock = threading.Lock()
    def __call__(cls, *args, **kwargs):
        with cls._lock:
            if cls not in cls._instances:
                cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]

class CICIDSPredictionStrategy(PredictionStrategy, metaclass=SingletonMeta):
    def __init__(self):
        import joblib
        try:
            self.model = joblib.load(settings.CICIDS_MODEL_PATH)
            logger.info("Loaded CICIDS model from %s", settings.CICIDS_MODEL_PATH)
        except Exception as e:
            logger.error("Failed to load CICIDS model: %s", e)
            raise
    def predict(self, features: Dict[str, Any]) -> float:
        X = [list(features.values())]
        return self.model.predict_proba(X)[0][1]

class LANLPredictionStrategy(PredictionStrategy, metaclass=SingletonMeta):
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
        timestamp = int(features["time"])
        user = features["user"]
        computer = features["computer"]
        user_encoded = self.user_encoder.transform([user])[0]
        computer_encoded = self.computer_encoder.transform([computer])[0]
        return [[timestamp, user_encoded, computer_encoded]]
    def predict(self, features: Dict[str, Any]) -> float:
        X = self.preprocess(features)
        pred = self.model.predict(X)[0]
        return 1.0 if pred == -1 else 0.0

class PredictionFactory:
    @staticmethod
    def get_strategy(model_name: str) -> PredictionStrategy:
        if model_name == "cicids":
            return CICIDSPredictionStrategy()
        elif model_name == "lanl":
            return LANLPredictionStrategy()
        else:
            raise ValueError(f"Unknown model name: {model_name}")
