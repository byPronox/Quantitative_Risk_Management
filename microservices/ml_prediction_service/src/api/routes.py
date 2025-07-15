"""
ML Prediction Service API Routes.
"""
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
import logging

from services.prediction_service import PredictionFactory, PredictionStrategy
from models.schemas import (
    CICIDSFeatures, LANLFeatures, CombinedFeatures,
    PredictionResponse, CombinedPredictionResponse, HealthResponse
)
from controllers.prediction_controller import PredictionController

router = APIRouter()
logger = logging.getLogger(__name__)

# Dependency injection for prediction controller
def get_prediction_controller() -> PredictionController:
    """Get prediction controller instance."""
    return PredictionController()

# Dependency injection for prediction strategies
def get_cicids_strategy() -> PredictionStrategy:
    """Get CICIDS prediction strategy."""
    return PredictionFactory.get_strategy("cicids")

def get_lanl_strategy() -> PredictionStrategy:
    """Get LANL prediction strategy.""" 
    return PredictionFactory.get_strategy("lanl")

@router.get("/health", response_model=HealthResponse)
def health_check():
    """Health check endpoint."""
    try:
        available_models = PredictionFactory.get_available_models()
        
        # Test if models can be loaded
        models_loaded = []
        for model in available_models:
            try:
                PredictionFactory.get_strategy(model)
                models_loaded.append(model)
            except Exception as e:
                logger.warning("Model %s failed to load: %s", model, e)
        
        return HealthResponse(
            status="healthy" if models_loaded else "unhealthy",
            models_loaded=models_loaded,
            service="ml-prediction-service"
        )
    except Exception as e:
        logger.error("Health check failed: %s", e)
        raise HTTPException(status_code=500, detail="Health check failed")

@router.post("/predict/cicids", response_model=PredictionResponse)
async def predict_cicids(
    features: CICIDSFeatures,
    controller: PredictionController = Depends(get_prediction_controller)
):
    """
    Predict using CICIDS model.
    
    Args:
        features: Network traffic features for CICIDS model
        controller: Prediction controller instance
        
    Returns:
        PredictionResponse: Prediction result with probability
    """
    try:
        return await controller.predict_cicids(features)
    except Exception as e:
        logger.error("CICIDS prediction endpoint failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

@router.post("/predict/lanl", response_model=PredictionResponse)
async def predict_lanl(
    features: LANLFeatures,
    controller: PredictionController = Depends(get_prediction_controller)
):
    """
    Predict using LANL model.
    
    Args:
        features: User activity features for LANL model
        controller: Prediction controller instance
        
    Returns:
        PredictionResponse: Prediction result with probability
    """
    try:
        return await controller.predict_lanl(features)
    except Exception as e:
        logger.error("LANL prediction endpoint failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

@router.post("/predict/combined", response_model=CombinedPredictionResponse)
async def predict_combined(
    features: CombinedFeatures,
    controller: PredictionController = Depends(get_prediction_controller)
):
    """
    Combined prediction using both CICIDS and LANL models.
    
    Args:
        features: Combined features for both models
        controller: Prediction controller instance
        
    Returns:
        CombinedPredictionResponse: Combined prediction result
    """
    try:
        return await controller.predict_combined(features)
    except Exception as e:
        logger.error("Combined prediction endpoint failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Combined prediction failed: {str(e)}")

@router.get("/models")
def get_available_models():
    """Get list of available models."""
    try:
        return {
            "models": PredictionFactory.get_available_models(),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error("Failed to get available models: %s", e)
        raise HTTPException(status_code=500, detail="Failed to get available models")

@router.get("/models/{model_name}/info")
def get_model_info(
    model_name: str,
    controller: PredictionController = Depends(get_prediction_controller)
):
    """Get information about a specific model."""
    try:
        info = controller.get_model_info(model_name)
        return {
            "model_info": info,
            "timestamp": datetime.utcnow().isoformat()
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("Failed to get model info: %s", e)
        raise HTTPException(status_code=500, detail="Failed to get model information")
