# 🧠 ML Prediction Service

Microservicio de **Machine Learning** para predicción de riesgos de ciberseguridad usando modelos entrenados con datasets CICIDS2017 y LANL.

## 🏗️ Arquitectura

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│   Backend   │ ──── │ ML Service  │ ──── │   Models    │
│   (Proxy)   │ HTTP │  (FastAPI)  │      │  (.pkl)     │
└─────────────┘      └─────────────┘      └─────────────┘
```

## ✨ Características

- **Predicción CICIDS** para detección de intrusiones en red
- **Predicción LANL** para anomalías de autenticación
- **Predicción Combinada** usando múltiples modelos
- **Patrón Strategy** para modelos intercambiables
- **Patrón Singleton** para carga eficiente de modelos
- **Isolation Forest** para detección de outliers

## 📦 Tecnologías

| Tecnología | Uso |
|------------|-----|
| Python 3.11 | Runtime |
| FastAPI | API REST |
| Scikit-learn | Machine Learning |
| Pandas | Procesamiento de datos |
| NumPy | Cálculos numéricos |
| Joblib | Serialización de modelos |

## 🚀 Quick Start

### Docker
```bash
docker build -t ml-prediction-service .
docker run -p 8001:8001 -v ./models:/app/src/models ml-prediction-service
```

### Desarrollo Local
```bash
pip install -r requirements.txt
uvicorn src.main:app --host 0.0.0.0 --port 8001 --reload
```

## 🔧 Configuración

### Variables de Entorno

```env
# Server
PORT=8001

# Model Paths
CICIDS_MODEL_PATH=/app/src/models/rf_cicids2017_model.pkl
LANL_MODEL_PATH=/app/src/models/isolation_forest_model.pkl
```

## 📡 API Endpoints

### POST /predict/cicids
Predicción usando modelo CICIDS2017.

**Request:**
```json
{
  "features": {
    "duration": 0.5,
    "protocol_type": "tcp",
    "src_bytes": 1024,
    "dst_bytes": 2048,
    "flag": "SF",
    "land": 0,
    "wrong_fragment": 0,
    "urgent": 0
  }
}
```

**Response:**
```json
{
  "model": "cicids",
  "prediction": "normal",
  "probability": 0.95,
  "risk_level": "LOW",
  "confidence": "HIGH"
}
```

### POST /predict/lanl
Predicción usando modelo LANL.

**Request:**
```json
{
  "features": {
    "user": "user123",
    "source_computer": "C123",
    "dest_computer": "C456",
    "auth_type": "Negotiate",
    "logon_type": "Interactive",
    "success": true
  }
}
```

**Response:**
```json
{
  "model": "lanl",
  "prediction": "anomaly",
  "anomaly_score": 0.85,
  "risk_level": "HIGH"
}
```

### POST /predict/combined
Predicción combinada usando múltiples modelos.

**Response:**
```json
{
  "cicids_result": {...},
  "lanl_result": {...},
  "combined_risk_score": 0.72,
  "combined_risk_level": "HIGH",
  "recommendations": [
    "Investigate authentication anomaly",
    "Review network traffic patterns"
  ]
}
```

### GET /health
Health check del servicio.

```json
{
  "status": "healthy",
  "models_loaded": {
    "cicids": true,
    "lanl": true
  }
}
```

## 🧠 Modelos

### CICIDS2017 (Random Forest)
- **Dataset:** CICIDS2017 Intrusion Detection
- **Algoritmo:** Random Forest Classifier
- **Features:** 78 características de tráfico de red
- **Clases:** Normal, DoS, DDoS, PortScan, Botnet, etc.

### LANL (Isolation Forest)
- **Dataset:** LANL Authentication Dataset
- **Algoritmo:** Isolation Forest
- **Features:** User, Computer, Auth Type, Logon Type
- **Output:** Anomaly Score (-1 = anomaly, 1 = normal)

## 📊 Estructura del Proyecto

```
ml_prediction_service/
├── src/
│   ├── main.py              # FastAPI entry point
│   ├── interfaces/
│   │   └── prediction_strategy.py  # Abstract strategy
│   ├── services/
│   │   ├── cicids_service.py       # CICIDS implementation
│   │   └── lanl_service.py         # LANL implementation
│   └── models/
│       ├── rf_cicids2017_model.pkl
│       └── isolation_forest_model.pkl
├── requirements.txt
└── Dockerfile
```

## 🎯 Patrones de Diseño

### Strategy Pattern
```python
class PredictionStrategy(ABC):
    @abstractmethod
    def predict(self, features: dict) -> dict:
        pass

class CICIDSStrategy(PredictionStrategy):
    def predict(self, features: dict) -> dict:
        # CICIDS-specific prediction
        pass
```

### Singleton Pattern
```python
class ModelLoader:
    _instance = None
    _models = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
```

## 🐳 Docker

### Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

ENV PYTHONPATH=/app/src
EXPOSE 8001

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
```

### Volume para Modelos
```yaml
volumes:
  - ./microservices/ml_prediction_service/src/models:/app/src/models
```

## 📚 Referencias

### CICIDS2017
- Iman Sharafaldin, Arash Habibi Lashkari, and Ali A. Ghorbani
- "Toward Generating a New Intrusion Detection Dataset and Intrusion Traffic Characterization"
- ICISSP 2018

### LANL Dataset
- Los Alamos National Laboratory
- "User-computer authentication associations in time"
- CC0 License

---

## 📄 Licencia

MIT License © 2025
