# 🛡️ QRMS - Quantitative Risk Management System

Sistema de **Gestión de Riesgos Cuantitativo** basado en microservicios para evaluación y mitigación de riesgos de ciberseguridad, potenciado por **Machine Learning**, **escaneo de vulnerabilidades** y arquitectura **Cloud-Native**.

![Demostración del Sistema](docs/images/demo.png)

---

## ✨ Características Principales

| Feature | Descripción |
|---------|-------------|
| 🔐 **Autenticación JWT** | Sistema de login seguro con tokens JWT |
| 🎯 **Predicción ML** | Modelos entrenados (CICIDS, LANL) para predicción de riesgos |
| 🛡️ **Integración NVD** | Búsqueda de vulnerabilidades en la Base de Datos Nacional |
| 🔍 **Escaneo Nmap** | Escaneo de redes con detección de servicios y vulnerabilidades |
| 🐰 **Colas RabbitMQ** | Procesamiento asíncrono de escaneos y análisis |
| 🌐 **Kong Gateway** | API Gateway para enrutamiento y rate limiting |
| 🐘 **Supabase** | Base de datos PostgreSQL en la nube |
| 🐳 **Docker** | Completamente contenerizado con Docker Compose |

---

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND (React)                                │
│                           http://localhost:5173                              │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           KONG API GATEWAY                                   │
│                           http://localhost:8080                              │
│  • Rate Limiting  • CORS  • Routing  • Load Balancing                       │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │
            ┌─────────────────────────┼─────────────────────────┐
            │                         │                         │
            ▼                         ▼                         ▼
┌───────────────────┐   ┌───────────────────┐   ┌───────────────────┐
│  BACKEND (FastAPI)│   │   NVD SERVICE     │   │  NMAP SCANNER     │
│   :8000           │   │   :8002           │   │  :8004            │
│  ─────────────────│   │  ─────────────────│   │  ─────────────────│
│  • Auth/JWT       │   │  • CVE Search     │   │  • Network Scan   │
│  • Risk Analysis  │   │  • Vuln Database  │   │  • Port Detection │
│  • ML Proxy       │   │                   │   │  • Service ID     │
└─────────┬─────────┘   └─────────┬─────────┘   └─────────┬─────────┘
          │                       │                       │
          ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              RABBITMQ                                        │
│                 Local: localhost:5672  |  Cloud: CloudAMQP                   │
└─────────────────────────────────────────────────────────────────────────────┘
          │                                                │
          ▼                                                ▼
┌───────────────────┐                         ┌───────────────────┐
│  ML PREDICTION    │                         │  SUPABASE         │
│  SERVICE :8001    │                         │  PostgreSQL Cloud │
│  ─────────────────│                         │  ─────────────────│
│  • CICIDS Model   │                         │  • Users          │
│  • LANL Model     │                         │  • Risk Analyses  │
│  • Isolation Forest│                        │  • Nmap Jobs      │
└───────────────────┘                         │  • NVD Jobs       │
                                              └───────────────────┘
```

---

## 🚀 Quick Start

### Prerrequisitos
- Docker & Docker Compose
- Git

### 1. Clonar el repositorio
```bash
git clone https://github.com/byPronox/Quantitative_Risk_Management.git
cd Quantitative_Risk_Management
```

### 2. Configurar variables de entorno
```bash
cp .env.example .env
# Editar .env con tus credenciales
```

### 3. Iniciar servicios
```bash
docker-compose up --build
```

### 4. Acceder a la aplicación
- **Frontend:** http://localhost:5173
- **Kong Gateway:** http://localhost:8080
- **Backend API:** http://localhost:8000/api/v1/docs
- **RabbitMQ:** http://localhost:15672 (guest/guest)

### Credenciales por defecto
```
Usuario: qrms
Contraseña: qrms
```

---

## 📂 Estructura del Proyecto

```
Quantitative_Risk_Management/
├── backend/                    # API Principal (FastAPI)
│   └── src/
│       ├── config/            # Configuración (database, settings)
│       ├── controllers/       # Endpoints (auth, risk, nmap, nvd)
│       ├── models/            # Modelos (Pydantic, SQLAlchemy)
│       ├── services/          # Lógica de negocio
│       ├── repositories/      # Acceso a datos
│       └── main.py
│
├── frontend/                   # UI (React + Vite)
│   └── src/
│       ├── components/        # Componentes reutilizables
│       ├── pages/             # Páginas (Login, Scan, Reports)
│       ├── context/           # Context API (AuthContext)
│       ├── services/          # Llamadas API
│       └── App.jsx
│
├── microservices/
│   ├── ml_prediction_service/ # Servicio ML (Python)
│   ├── nmap_scanner/          # Escáner Nmap (Node.js)
│   └── nvd_service/           # Servicio NVD (Python)
│
├── docker-compose.yml         # Orquestación de contenedores
├── kong.yml                   # Configuración Kong Gateway
└── .env                       # Variables de entorno
```

---

## 🔐 Autenticación

El sistema usa **JWT (JSON Web Tokens)** para autenticación.

### Endpoints de Auth
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/v1/auth/login` | Login con usuario/contraseña |
| GET | `/api/v1/auth/me` | Obtener usuario actual |
| POST | `/api/v1/auth/verify` | Verificar token válido |
| POST | `/api/v1/auth/logout` | Cerrar sesión |

### Ejemplo de Login
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "qrms", "password": "qrms"}'
```

Respuesta:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "username": "qrms",
  "expires_in": 86400
}
```

---

## 🔍 Escaneo de Red (Nmap)

El módulo de escaneo utiliza Nmap para detectar servicios y vulnerabilidades.

### Flujo del Escaneo
```
Frontend → Kong Gateway → Backend → RabbitMQ → Nmap Worker → PostgreSQL
```

### Endpoints
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/v1/nmap/scan` | Iniciar escaneo (async) |
| GET | `/api/v1/nmap/job/{job_id}` | Obtener estado del job |
| GET | `/api/v1/nmap/health` | Estado del servicio |

### Ejemplo de Escaneo
```bash
# Iniciar escaneo
curl -X POST http://localhost:8000/api/v1/nmap/scan \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"target": "192.168.1.1"}'

# Respuesta
{
  "job_id": "nmap_abc123",
  "status": "queued",
  "message": "Scan queued successfully"
}
```

---

## 🛡️ Búsqueda de Vulnerabilidades (NVD)

Integración con la **National Vulnerability Database** del NIST.

### Endpoints
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/v1/nvd/search?keyword=apache` | Buscar CVEs |
| POST | `/api/v1/nvd/analyze` | Analizar vulnerabilidades |
| GET | `/api/v1/nvd/job/{job_id}` | Estado del análisis |

---

## 🧠 Predicción ML

Modelos de Machine Learning para predicción de riesgos.

### Modelos Disponibles
- **CICIDS2017**: Detección de intrusiones en red
- **LANL**: Detección de anomalías de autenticación
- **Isolation Forest**: Detección de outliers

### Endpoints
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/v1/predict/cicids` | Predicción CICIDS |
| POST | `/api/v1/predict/lanl` | Predicción LANL |
| POST | `/api/v1/predict/combined` | Predicción combinada |

---

## ⚙️ Configuración

### Variables de Entorno (.env)

```env
# Database (Supabase)
DATABASE_URL=postgresql://user:pass@host:5432/db

# JWT Authentication
JWT_SECRET_KEY=your-secret-key

# RabbitMQ
RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/

# NVD API
NVD_API_KEY=your-nvd-api-key

# Kong Gateway
KONG_PROXY_URL=http://localhost:8080

# Frontend
VITE_API_URL=http://localhost:8000
```

### Producción vs Desarrollo

| Variable | Desarrollo | Producción |
|----------|------------|------------|
| RABBITMQ_URL | Docker local | CloudAMQP |
| DATABASE_URL | Supabase | Supabase |
| KONG_PROXY_URL | localhost:8080 | Kong Cloud |

---

## 🐳 Docker Services

| Servicio | Puerto | Descripción |
|----------|--------|-------------|
| frontend | 5173 | React + Vite |
| backend | 8000 | FastAPI |
| kong | 8080/8081 | API Gateway |
| rabbitmq | 5672/15672 | Message Queue |
| nvd-service | 8002 | NVD Integration |
| nmap-scanner-service | 8004 | Network Scanner |
| ml-prediction-service | 8001 | ML Models |

### Comandos Útiles
```bash
# Iniciar todos los servicios
docker-compose up -d

# Ver logs
docker-compose logs -f backend

# Reconstruir un servicio
docker-compose up -d --build frontend

# Detener todo
docker-compose down

# Limpiar volúmenes
docker-compose down -v
```

---

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

---

## 📊 API Documentation

- **Swagger UI:** http://localhost:8000/api/v1/docs
- **ReDoc:** http://localhost:8000/api/v1/redoc

---

## 🔒 Seguridad

- ✅ Autenticación JWT con bcrypt
- ✅ CORS configurado en Kong
- ✅ Rate limiting en API Gateway
- ✅ Variables sensibles en .env
- ✅ SSL/TLS para conexiones cloud

---

## 👨‍💻 Autores

**Stefan Jativa** — [@byPronox](https://github.com/byPronox)  
*Machine Learning | Software Engineer*

**Justin Gomezcoello** — [@JustinGomezcoello](https://github.com/JustinGomezcoello)  
*Automation | Software Engineer*

---

## 📄 Licencia

MIT License © 2025

---

## 📚 Referencias

### Datasets
- **CICIDS2017**: [Canadian Institute for Cybersecurity](https://www.unb.ca/cic/datasets/ids-2017.html)
- **LANL Auth Dataset**: [Los Alamos National Laboratory](https://csr.lanl.gov/data/auth/)

### APIs
- **NVD API**: [NIST National Vulnerability Database](https://nvd.nist.gov/developers)
