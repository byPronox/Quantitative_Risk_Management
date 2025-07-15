"""
Abstract base class for prediction strategies (Strategy Pattern).
"""
from abc import ABC, abstractmethod
from typing import Any, Dict

class PredictionStrategy(ABC):
    """Abstract base class for prediction strategies implementing Strategy pattern."""
    
    @abstractmethod
    def predict(self, features: Dict[str, Any]) -> float:
        """
        Predict risk probability based on input features.
        
        Args:
            features: Dictionary containing model-specific features
            
        Returns:
            float: Risk probability between 0.0 and 1.0
        """
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the model.
        
        Returns:
            dict: Model information including name, version, etc.
        """
        pass
