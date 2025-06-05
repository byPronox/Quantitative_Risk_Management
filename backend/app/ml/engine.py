import joblib
import os

# Carga los modelos y encoders ya entrenados (guardados juntos en el .pkl)
cicids_model = joblib.load(os.path.join(os.path.dirname(__file__), "rf_cicids2017_model.pkl"))
lanl_bundle = joblib.load(os.path.join(os.path.dirname(__file__), "isolation_forest_model.pkl"))
lanl_model = lanl_bundle["model"]
user_encoder = lanl_bundle["user_encoder"]
computer_encoder = lanl_bundle["computer_encoder"]

def predict_cicids(features: dict):
    X = [list(features.values())]
    return cicids_model.predict_proba(X)[0][1]

def preprocess_lanl_features(features: dict):
    timestamp = int(features["time"])
    user = features["user"]
    computer = features["computer"]
    user_encoded = user_encoder.transform([user])[0]
    computer_encoded = computer_encoder.transform([computer])[0]
    return [[timestamp, user_encoded, computer_encoded]]

def predict_lanl(features: dict):
    X = preprocess_lanl_features(features)
    pred = lanl_model.predict(X)[0]
    return 1.0 if pred == -1 else 0.0