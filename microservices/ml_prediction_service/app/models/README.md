# Model Files Directory

This directory should contain the trained ML model files:

- `rf_cicids2017_model.pkl` - Random Forest model for CICIDS network intrusion detection
- `isolation_forest_model.pkl` - Isolation Forest model bundle for LANL user activity anomaly detection

## Model Requirements

### CICIDS Model
- Should be a scikit-learn RandomForestClassifier
- Trained on CICIDS2017 dataset
- Expects network traffic features as input

### LANL Model
- Should be a scikit-learn IsolationForest in a bundle format
- Bundle should contain:
  - `model`: The trained IsolationForest
  - `user_encoder`: LabelEncoder for user identifiers
  - `computer_encoder`: LabelEncoder for computer identifiers
- Trained on LANL network activity data

## Loading
Models are loaded automatically when the service starts using the Singleton pattern to ensure they're only loaded once per process.
