# ML Models

This directory contains the trained machine learning models used by the ML Prediction Service.

## Models Included

### 1. CICIDS Model (`rf_cicids2017_model.pkl`)
- **Type**: Random Forest Classifier
- **Purpose**: Network traffic analysis and intrusion detection
- **Dataset**: CICIDS2017
- **Features**: Network flow features (flow duration, packet counts, bytes, etc.)
- **Output**: Attack probability (0.0 to 1.0)

### 2. LANL Model (`isolation_forest_model.pkl`)
- **Type**: Isolation Forest (Anomaly Detection)
- **Purpose**: User behavior analysis and insider threat detection
- **Dataset**: LANL Cybersecurity Dataset
- **Features**: User activity (timestamp, user ID, computer ID)
- **Output**: Anomaly probability (0.0 for normal, 1.0 for anomaly)
- **Components**: 
  - Model: Isolation Forest
  - User Encoder: Label encoder for user IDs
  - Computer Encoder: Label encoder for computer IDs

## Model Format

All models are saved using Python's joblib library and are compatible with scikit-learn.

### CICIDS Model Structure
```python
# Direct scikit-learn RandomForestClassifier
model = joblib.load('rf_cicids2017_model.pkl')
prediction = model.predict_proba(features)[0][1]  # Get attack probability
```

### LANL Model Structure
```python
# Bundle containing model and encoders
bundle = joblib.load('isolation_forest_model.pkl')
model = bundle["model"]
user_encoder = bundle["user_encoder"]
computer_encoder = bundle["computer_encoder"]
```

## Usage in Docker

When running in Docker, these models are mounted to `/app/models/` directory:

```dockerfile
COPY models/ /app/models/
```

## Configuration

Model paths are configured via environment variables:
- `CICIDS_MODEL_PATH`: Path to CICIDS model
- `LANL_MODEL_PATH`: Path to LANL model
- `MODELS_BASE_PATH`: Base directory for models

## Security Considerations

- Models contain trained parameters and should be protected
- Consider encrypting models for production deployments
- Validate model integrity before loading
- Monitor model performance and retrain periodically
