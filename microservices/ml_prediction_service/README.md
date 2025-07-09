# ML Prediction Microservice

A dedicated microservice for handling machine learning predictions using CICIDS and LANL models.

## Features
- CICIDS model predictions
- LANL model predictions  
- Combined predictions
- Singleton pattern for model loading
- Strategy pattern for different models

## Endpoints
- `POST /predict/cicids` - CICIDS predictions
- `POST /predict/lanl` - LANL predictions
- `POST /predict/combined` - Combined model predictions
- `GET /health` - Health check

## Architecture
- **Interfaces**: Abstract prediction strategy
- **Services**: Concrete prediction implementations
- **Models**: ML model files and loading logic
- **API**: FastAPI endpoints
