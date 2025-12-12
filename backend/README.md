# Backend - QRMS API Gateway

API principal del sistema QRMS construida con **FastAPI**, implementando arquitectura limpia con autenticación JWT, integración con microservicios y base de datos Supabase.

## 🏗️ Arquitectura

```
backend/
├── src/
│   ├── config/
│   │   ├── settings.py          # Configuración centralizada (Pydantic Settings)
│   │   └── database.py          # SQLAlchemy + Supabase
│   │
│   ├── controllers/
│   │   ├── auth_controller.py   # 🔐 Autenticación JWT
│   │   ├── health_controller.py # Health checks
│   │   ├── risk_controller.py   # Análisis de riesgos
│   │   ├── nmap_controller.py   # Proxy a NMAP service
│   │   ├── nvd_controller.py    # Proxy a NVD service
│   │   └── gateway_controller.py
│   │
│   ├── models/
│   │   ├── database_models.py   # SQLAlchemy Models (User, RiskAnalysis, etc.)
│   │   └── risk_models.py       # Pydantic Schemas
│   │
│   ├── services/
│   │   ├── risk_service.py      # Lógica de negocio
│   │   ├── ml_service.py        # Proxy a ML service
│   │   ├── nvd_service.py       # Cliente NVD API
│   │   └── nmap_queue_service.py # RabbitMQ publisher
│   │
│   ├── repositories/
│   │   └── risk_repository.py   # Data Access Layer
│   │
│   ├── middleware/
│   │   ├── error_handler.py     # Exception handling
│   │   └── logging_middleware.py
│   │
│   └── main.py                  # FastAPI app entry point
│
├── requirements.txt
├── Dockerfile
└── .env
```

## 🚀 Características

- **Autenticación JWT** con passlib/bcrypt
- **SQLAlchemy ORM** con Supabase PostgreSQL
- **RabbitMQ** para colas de mensajes
- **Arquitectura Limpia** (Controllers → Services → Repositories)
- **Middleware** para logging y manejo de errores
- **Pydantic** para validación de datos

## 📦 Dependencias Principales

```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
pydantic==2.5.0
passlib[bcrypt]==1.7.4
python-jose[cryptography]==3.3.0
pika==1.3.2
httpx==0.25.2
```

## 🔐 Autenticación

### Modelo de Usuario
```python
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    email = Column(String(100), unique=True)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    last_login = Column(DateTime)
```

### Endpoints
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/v1/auth/login` | Login con JSON |
| POST | `/api/v1/auth/login/form` | Login OAuth2 compatible |
| GET | `/api/v1/auth/me` | Usuario actual (requiere token) |
| POST | `/api/v1/auth/verify` | Verificar token |
| POST | `/api/v1/auth/register` | Registro de usuario |
| POST | `/api/v1/auth/logout` | Cerrar sesión |

### Usuario por Defecto
Se crea automáticamente al iniciar:
```
Username: qrms
Password: qrms
```

## 🔧 Configuración

### Variables de Entorno

```env
# API
API_HOST=0.0.0.0
API_PORT=8000
API_VERSION=v1

# Database (Supabase)
DATABASE_URL=postgresql://postgres:password@db.xxx.supabase.co:5432/postgres

# JWT
JWT_SECRET_KEY=your-secret-key-here

# RabbitMQ
RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/

# Microservices
ML_SERVICE_URL=http://ml-prediction-service:8001
NVD_SERVICE_URL=http://nvd-service:8002
NMAP_SERVICE_URL=http://nmap-scanner-service:8004

# NVD API
NVD_API_KEY=your-nvd-api-key
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
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Build & Run
```bash
# Build
docker build -t qrms-backend .

# Run
docker run -p 8000:8000 --env-file .env qrms-backend
```

## 📡 API Endpoints

### Health
```bash
GET /api/v1/health
GET /health
```

### Risk Analysis
```bash
POST /api/v1/risk/analyze
GET  /api/v1/risk/analyses
GET  /api/v1/risk/analyses/{id}
```

### NMAP Proxy
```bash
POST /api/v1/nmap/scan
GET  /api/v1/nmap/job/{job_id}
GET  /api/v1/nmap/health
```

### NVD Proxy
```bash
GET  /api/v1/nvd/search?keyword=apache
POST /api/v1/nvd/analyze
GET  /api/v1/nvd/job/{job_id}
```

### ML Prediction Proxy
```bash
POST /api/v1/predict/cicids
POST /api/v1/predict/lanl
POST /api/v1/predict/combined
```

## 📊 Base de Datos (Supabase)

### Tablas
| Tabla | Descripción |
|-------|-------------|
| `users` | Usuarios del sistema |
| `risk_analyses` | Análisis de riesgo realizados |
| `assets` | Activos registrados |
| `vulnerabilities` | Vulnerabilidades encontradas |
| `nvd_jobs` | Jobs de análisis NVD |
| `nmap_jobs` | Jobs de escaneo Nmap |

### Inicialización
Las tablas se crean automáticamente al iniciar la aplicación:
```python
@app.on_event("startup")
async def startup_event():
    await init_db()  # Crea tablas con SQLAlchemy
    seed_default_user(db)  # Crea usuario qrms/qrms
```

## 🧪 Testing

```bash
# Instalar dependencias de test
pip install pytest pytest-asyncio httpx

# Ejecutar tests
pytest tests/ -v
```

## 📝 Logging

El sistema incluye middleware de logging que registra:
- Todas las requests entrantes
- Tiempo de respuesta
- Errores y excepciones
- Operaciones de autenticación

```python
# Configuración
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
```

## 🔗 Integración con Microservicios

El backend actúa como **API Gateway** para los microservicios:

```
Frontend → Backend (FastAPI) → Microservice
                ↓
           RabbitMQ (para jobs async)
```

### Comunicación
- **HTTP/REST**: Para consultas síncronas
- **RabbitMQ**: Para jobs asíncronos (scans, análisis)
- **PostgreSQL**: Almacenamiento compartido de estado

---

## 📄 Licencia

MIT License © 2025
