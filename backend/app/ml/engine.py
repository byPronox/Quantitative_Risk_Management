import joblib
import os
import pandas as pd

CICIDS_MODEL_PATH = os.path.join(os.path.dirname(__file__), "rf_cicids2017_model.pkl")

def predict_cicids(features: dict) -> float:
    if not os.path.exists(CICIDS_MODEL_PATH):
        return 0.0
    model = joblib.load(CICIDS_MODEL_PATH)
    X = pd.DataFrame([features])
    pred = model.predict_proba(X)
    return float(pred[0][1])  # Probabilidad de ataque