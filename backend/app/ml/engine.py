from services.prediction_service import PredictionFactory
from interfaces.prediction_strategy import PredictionStrategy

# --- Old API for compatibility ---
def predict_cicids(features: dict):
    return PredictionFactory.get_strategy("cicids").predict(features)

def predict_lanl(features: dict):
    return PredictionFactory.get_strategy("lanl").predict(features)