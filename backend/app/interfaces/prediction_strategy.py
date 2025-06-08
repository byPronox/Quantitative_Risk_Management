"""
Abstract base class for prediction strategies (Strategy Pattern).
"""
from abc import ABC, abstractmethod
from typing import Any, Dict

class PredictionStrategy(ABC):
    @abstractmethod
    def predict(self, features: Dict[str, Any]) -> float:
        pass
