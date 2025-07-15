"""
Prediction controllers for ML Prediction Service.
"""
import logging
from datetime import datetime
from typing import Dict, Any

from ..services.prediction_service import PredictionFactory
from ..models.schemas import (
    CICIDSFeatures, LANLFeatures, CombinedFeatures,
    PredictionResponse, CombinedPredictionResponse
)

logger = logging.getLogger(__name__)

class PredictionController:
    """Controller for handling prediction requests."""
    
    def __init__(self):
        self.factory = PredictionFactory()
    
    async def predict_cicids(self, features: CICIDSFeatures) -> PredictionResponse:
        """
        Handle CICIDS prediction request.
        
        Args:
            features: CICIDS model features
            
        Returns:
            PredictionResponse: Prediction result
        """
        try:
            strategy = self.factory.get_strategy("cicids")
            features_dict = features.dict(by_alias=True)
            probability = strategy.predict(features_dict)
            
            return PredictionResponse(
                model="cicids",
                probability=probability,
                features=features_dict,
                timestamp=datetime.utcnow().isoformat()
            )
        except Exception as e:
            logger.error("CICIDS prediction failed: %s", e)
            raise
    
    async def predict_lanl(self, features: LANLFeatures) -> PredictionResponse:
        """
        Handle LANL prediction request.
        
        Args:
            features: LANL model features
            
        Returns:
            PredictionResponse: Prediction result
        """
        try:
            strategy = self.factory.get_strategy("lanl")
            features_dict = features.dict()
            probability = strategy.predict(features_dict)
            
            return PredictionResponse(
                model="lanl",
                probability=probability,
                features=features_dict,
                timestamp=datetime.utcnow().isoformat()
            )
        except Exception as e:
            logger.error("LANL prediction failed: %s", e)
            raise
    
    async def predict_combined(self, features: CombinedFeatures) -> CombinedPredictionResponse:
        """
        Handle combined prediction request.
        
        Args:
            features: Combined model features
            
        Returns:
            CombinedPredictionResponse: Combined prediction result
        """
        try:
            # Get predictions from both models
            cicids_strategy = self.factory.get_strategy("cicids")
            lanl_strategy = self.factory.get_strategy("lanl")
            
            cicids_features = features.cicids.dict(by_alias=True)
            lanl_features = features.lanl.dict()
            
            cicids_prob = cicids_strategy.predict(cicids_features)
            lanl_prob = lanl_strategy.predict(lanl_features)
            
            # Combine probabilities (simple average for now)
            combined_score = (cicids_prob + lanl_prob) / 2.0
            
            return CombinedPredictionResponse(
                cicids_probability=cicids_prob,
                lanl_probability=lanl_prob,
                combined_score=combined_score,
                timestamp=datetime.utcnow().isoformat()
            )
        except Exception as e:
            logger.error("Combined prediction failed: %s", e)
            raise
    
    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """
        Get model information.
        
        Args:
            model_name: Name of the model
            
        Returns:
            dict: Model information
        """
        try:
            strategy = self.factory.get_strategy(model_name)
            return strategy.get_model_info()
        except Exception as e:
            logger.error("Failed to get model info for %s: %s", model_name, e)
            raise
