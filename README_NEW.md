# 🛡️ Quantitative Risk Management System

A comprehensive cybersecurity risk management platform built with modern microservices architecture, featuring real-time vulnerability assessment, machine learning-based threat prediction, and enterprise-grade analytics.

![Quantitative Risk Management System Demo](docs/images/demo.png)

*Enterprise-grade cybersecurity risk management platform with microservices architecture*

---

## 🏗️ Architecture Overview

The system follows a **microservices architecture** pattern with the following components:

### 🔧 Core Microservices

- **🤖 ML Prediction Service** (`microservices/ml_prediction_service/`)
  - Machine learning-based threat prediction
  - CICIDS2017 model integration  
  - Isolation Forest anomaly detection
  - Async processing capabilities

- **🔍 NVD Vulnerability Service** (`microservices/nvd_service/`)
  - NVD API integration with Kong Gateway support
  - Real-time vulnerability data retrieval
  - Risk analysis and scoring
  - Queue-based processing

### 🚀 Infrastructure Services

- **🌐 Kong Gateway**: API proxy and management
- **📨 RabbitMQ**: Message queue for async processing
- **⚡ Redis**: Caching and session management
- **🗄️ PostgreSQL**: Primary database
- **💻 Frontend**: React-based dashboard

### 📦 Legacy Components (Migration Phase)

- **🏢 Backend** (`backend/`): Monolithic service being phased out

---

## 🚀 Quick Start

### Prerequisites

- 🐳 Docker and Docker Compose
- 📁 Git
- 🔑 Optional: Kong API key for enhanced NVD access

### Environment Setup

1. **Clone the repository:**
```bash
git clone <repository-url>
cd Quantitative_Risk_Management
```

2. **Copy environment configuration:**
```bash
# Windows PowerShell
Copy-Item .env.example .env

# Linux/macOS
cp .env.example .env
```

3. **Configure environment variables in `.env`:**
```env
# NVD API Configuration
NVD_API_KEY=your_nvd_api_key_here
KONG_PROXY_URL=your_kong_gateway_url
USE_KONG_NVD=true

# Kong Gateway Configuration
KONG_ADMIN_API=your_kong_admin_url
KONG_CONTROL_PLANE_ID=your_control_plane_id
KONG_TOKEN=your_kong_token
```

### 🏃‍♂️ Running the System

#### Option 1: Microservices Only (Recommended for Development)

**Windows:**
```powershell
.\microservices.ps1 start-micro
```

**Linux/macOS:**
```bash
./microservices.sh start-micro
```

#### Option 2: Full System (Production-like)

**Windows:**
```powershell
.\microservices.ps1 start-full
```

**Linux/macOS:**
```bash
./microservices.sh start-full
```

#### Option 3: Manual Docker Compose

```bash
# Microservices only
docker-compose -f docker-compose.microservices.yml up -d

# Full system
docker-compose up -d
```

---

## 📊 Service Endpoints

### 🤖 ML Prediction Service (Port 8001)
- **Health Check**: `GET /health`
- **Predict CICIDS**: `POST /api/v1/predict/cicids`
- **Predict Anomaly**: `POST /api/v1/predict/anomaly`
- **Models Info**: `GET /api/v1/models`

### 🔍 NVD Vulnerability Service (Port 8002)
- **Health Check**: `GET /api/v1/health`
- **Search Vulnerabilities**: `POST /api/v1/vulnerabilities/search`
- **Get CVE Details**: `GET /api/v1/vulnerabilities/{cve_id}`
- **Risk Analysis**: `POST /api/v1/analysis/risk`
- **Queue Job**: `POST /api/v1/queue/jobs`

### 💻 Frontend (Port 5173)
- **Dashboard**: `http://localhost:5173`
- **API Documentation**: Available through service endpoints

### 🔧 Infrastructure Services
- **RabbitMQ Management**: `http://localhost:15672` (guest/guest)
- **Redis**: `localhost:6379`
- **PostgreSQL**: `localhost:5432`

---

## 🛠️ Management Scripts

The project includes management scripts for easier development:

### Windows PowerShell (`microservices.ps1`)
```powershell
# Start microservices
.\microservices.ps1 start-micro

# Check service status  
.\microservices.ps1 status-micro

# View logs
.\microservices.ps1 logs nvd-service

# Run health checks
.\microservices.ps1 test

# Stop services
.\microservices.ps1 stop-micro
```

### Linux/macOS Bash (`microservices.sh`)
```bash
# Start microservices
./microservices.sh start-micro

# Check service status
./microservices.sh status-micro

# View logs
./microservices.sh logs nvd-service

# Run health checks
./microservices.sh test

# Stop services
./microservices.sh stop-micro
```

---

## 🔧 Development

### Project Structure

```
Quantitative_Risk_Management/
├── microservices/
│   ├── ml_prediction_service/      # 🤖 ML microservice
│   │   ├── app/
│   │   │   ├── interfaces/         # Strategy patterns
│   │   │   ├── services/           # Business logic
│   │   │   ├── api/               # FastAPI routes & schemas
│   │   │   ├── models/            # Data models
│   │   │   └── main.py
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── README.md
│   └── nvd_service/               # 🔍 NVD vulnerability service
│       ├── app/
│       │   ├── services/          # NVD API, risk analysis, queue
│       │   ├── api/              # FastAPI routes & schemas
│       │   ├── models/           # Data models
│       │   └── main.py
│       ├── Dockerfile
│       ├── requirements.txt
│       └── README.md
├── backend/                       # 📦 Legacy monolith (being phased out)
├── frontend/                      # 💻 React dashboard
├── docs/                         # 📚 Documentation
├── docker-compose.yml            # 🐳 Full system composition
├── docker-compose.microservices.yml  # 🔧 Microservices only
├── microservices.ps1            # 🪟 Windows management script
├── microservices.sh             # 🐧 Linux/macOS management script
└── README.md
```

### Adding New Microservices

1. Create service directory under `microservices/`
2. Follow the established patterns (interfaces, services, API layers)
3. Add Dockerfile and requirements.txt
4. Update docker-compose files
5. Add service to management scripts

### Design Patterns Used

- **🎯 Strategy Pattern**: Pluggable ML prediction algorithms
- **🔄 Singleton Pattern**: Model loading and caching
- **🏭 Factory Pattern**: Service instantiation
- **📚 Repository Pattern**: Data access abstraction
- **⚡ Circuit Breaker**: External API fault tolerance

---

## 🔐 Security

### API Security
- 🌐 Kong Gateway for API management and security
- 🔑 API key authentication for external services
- 🌍 CORS configuration for frontend access
- ✅ Input validation with Pydantic schemas

### Infrastructure Security
- 👤 Non-root Docker containers
- 💊 Health checks and monitoring
- 🔐 Environment variable management
- 🔒 Network isolation between services

---

## 📈 Monitoring & Observability

### Health Checks
All services provide `/health` endpoints for monitoring:
```bash
# Check all services
curl http://localhost:8001/health  # ML Service
curl http://localhost:8002/api/v1/health  # NVD Service
```

### Metrics
Services expose metrics for:
- ⏱️ Request/response times
- ✅❌ Success/error rates
- 📊 Queue sizes and processing times
- 💾 Resource utilization

### Logging
Structured logging with:
- 🔍 Request tracing
- ❌ Error tracking
- 📊 Performance metrics
- 📋 Business events

---

## 🧪 Testing

### Automated Health Checks
```bash
# Using management scripts
./microservices.sh test          # Linux/macOS
.\microservices.ps1 test        # Windows

# Manual testing
curl -f http://localhost:8001/health
curl -f http://localhost:8002/api/v1/health
```

### Integration Testing
```bash
# Test ML prediction
curl -X POST http://localhost:8001/api/v1/predict/cicids \
  -H "Content-Type: application/json" \
  -d '{"features": [0.1, 0.2, 0.3]}'

# Test NVD search
curl -X POST http://localhost:8002/api/v1/vulnerabilities/search \
  -H "Content-Type: application/json" \
  -d '{"keywords": "apache", "results_per_page": 5}'
```

---

## 🚧 Migration Status

The system is currently in migration from monolithic to microservices architecture:

### ✅ Completed
- 🤖 ML Prediction Service (fully functional)
- 🔍 NVD Vulnerability Service (fully functional)
- 🐳 Docker composition and orchestration
- 🛠️ Management scripts for development
- 💻 Frontend integration with microservices

### 🔄 In Progress
- 📦 Legacy backend deprecation
- 🌐 Complete Kong Gateway integration
- 🚀 Production deployment configuration

### 📋 Planned
- 📊 Monitoring and alerting setup
- 🔄 CI/CD pipeline integration
- ⚡ Load testing and performance optimization
- 🏢 Enterprise analytics microservice

---

## 🧱 Tech Stack

| Layer                | Technology                                    |
|---------------------|-----------------------------------------------|
| **Frontend**        | React, Tailwind CSS, Vite, Chart.js         |
| **Microservices**   | FastAPI, Python, Pydantic, uvicorn          |
| **ML/AI**           | Scikit-learn, joblib, CICIDS2017            |
| **Message Queue**   | RabbitMQ, pika                              |
| **Cache**           | Redis                                        |
| **Database**        | PostgreSQL                                   |
| **API Gateway**     | Kong Gateway                                 |
| **DevOps**          | Docker, Docker Compose                      |
| **Security**        | API keys, CORS, Input validation            |

---

## 🤝 Contributing

1. Follow the established microservices patterns
2. Ensure all services have proper health checks
3. Update documentation when adding features
4. Test with both development and production configurations

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 📞 Support

For questions or support:
1. 📋 Check service logs: `./microservices.sh logs <service-name>`
2. 💊 Verify service health: `./microservices.sh test`
3. 📚 Review documentation in `docs/` directory
4. 📖 Check individual microservice READMEs

---

## 🌟 Features Overview

- 🎯 **Advanced Risk Prediction** using trained ML models (CICIDS, LANL)
- 🧠 **Dynamic Programming Engine** for optimal decision-making
- 📊 **Interactive Dashboard** built with React + Tailwind CSS
- 🔄 **RESTful APIs** powered by FastAPI (Python)
- 🐳 **Fully Containerized** with Docker & Docker Compose
- 📁 **PostgreSQL Database** integration
- 📈 **Data Visualization** with Chart.js and custom SVG components
- 🛡️ **NVD Integration** with the National Vulnerability Database (NVD) API
- 🏛️ **Microservices Architecture** with API Gateway
- 🔍 **Comprehensive Vulnerability Search** with keyword-based filtering
- 📋 **Queue Management System** with RabbitMQ for asynchronous processing
- 🎛️ **Risk Assessment Configuration** with customizable thresholds
- 🏢 **Enterprise Asset Categorization** (Web Apps, Infrastructure, Databases, etc.)
- 📊 **Business Impact Analysis** with weighted scoring algorithms
- 📈 **Analysis History Tracking** for audit and compliance
- 🎨 **Modern Responsive UI** with tabbed interface and real-time updates
