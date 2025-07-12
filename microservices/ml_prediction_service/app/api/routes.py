"""
ML Prediction Service API Routes.
"""
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
import logging

from services.prediction_service import PredictionFactory, PredictionStrategy
from api.schemas import (
    CICIDSFeatures, LANLFeatures, CombinedFeatures,
    PredictionResponse, CombinedPredictionResponse, HealthResponse
)

router = APIRouter()
logger = logging.getLogger(__name__)

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
        return HealthResponse(
            status="healthy",
            models_loaded=available_models,
            service="ml-prediction-service"
        )
    except Exception as e:
        logger.error("Health check failed: %s", e)
        raise HTTPException(status_code=503, detail="Service unhealthy")

@router.post("/predict/cicids", response_model=PredictionResponse)
def predict_cicids(
    features: CICIDSFeatures,
    strategy: PredictionStrategy = Depends(get_cicids_strategy)
):
    """
    Predict risk using CICIDS model.
    
    Args:
        features: Network traffic features
        strategy: CICIDS prediction strategy (injected)
        
    Returns:
        PredictionResponse: Prediction result with probability
    """
    try:
        # Convert Pydantic model to dict
        feature_dict = features.dict()
        probability = strategy.predict(feature_dict)
        
        logger.info("CICIDS prediction successful: probability=%f", probability)
        
        return PredictionResponse(
            model="cicids",
            probability=probability,
            features=feature_dict,
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        logger.error("CICIDS prediction failed: %s", e)
        raise HTTPException(
            status_code=500, 
            detail=f"CICIDS prediction failed: {str(e)}"
        )

@router.post("/predict/lanl", response_model=PredictionResponse)
def predict_lanl(
    features: LANLFeatures,
    strategy: PredictionStrategy = Depends(get_lanl_strategy)
):
    """
    Predict anomaly using LANL model.
    
    Args:
        features: User activity features
        strategy: LANL prediction strategy (injected)
        
    Returns:
        PredictionResponse: Prediction result with probability
    """
    try:
        # Convert Pydantic model to dict
        feature_dict = features.dict()
        probability = strategy.predict(feature_dict)
        
        logger.info("LANL prediction successful: probability=%f", probability)
        
        return PredictionResponse(
            model="lanl",
            probability=probability,
            features=feature_dict,
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        logger.error("LANL prediction failed: %s", e)
        raise HTTPException(
            status_code=500,
            detail=f"LANL prediction failed: {str(e)}"
        )

@router.post("/predict/combined", response_model=CombinedPredictionResponse)
def predict_combined(
    features: CombinedFeatures,
    cicids_strategy: PredictionStrategy = Depends(get_cicids_strategy),
    lanl_strategy: PredictionStrategy = Depends(get_lanl_strategy)
):
    """
    Combined prediction using both CICIDS and LANL models.
    
    Args:
        features: Combined features for both models
        cicids_strategy: CICIDS prediction strategy (injected)
        lanl_strategy: LANL prediction strategy (injected)
        
    Returns:
        CombinedPredictionResponse: Combined prediction result
    """
    try:
        # Get predictions from both models
        cicids_prob = cicids_strategy.predict(features.cicids.dict())
        lanl_prob = lanl_strategy.predict(features.lanl.dict())
        
        # Calculate combined score (simple average)
        combined_score = (cicids_prob + lanl_prob) / 2
        
        logger.info(
            "Combined prediction successful: cicids=%f, lanl=%f, combined=%f",
            cicids_prob, lanl_prob, combined_score
        )
        
        return CombinedPredictionResponse(
            cicids_probability=cicids_prob,
            lanl_probability=lanl_prob,
            combined_score=combined_score,
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        logger.error("Combined prediction failed: %s", e)
        raise HTTPException(
            status_code=500,
            detail=f"Combined prediction failed: {str(e)}"
        )
