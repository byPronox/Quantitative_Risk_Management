# ⚠️ Quantitative Risk Management System

A full-stack, microservices-based application for **quantitative risk assessment and mitigation**, powered by **Machine Learning** and **Dynamic Programming**. This system predicts potential risks, evaluates their impact, and recommends optimal mitigation strategies using intelligent algorithms and data-driven insights.

![Quantitative Risk Management System Demo](docs/images/demo.png)

*Screenshot: NVD Vulnerability Management System with comprehensive risk analysis dashboard, featuring tabbed interface for vulnerability search, risk assessment configuration, and enterprise-level asset categorization.*

---

## ✨ Features

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

---

## 🧱 Tech Stack

| Layer        | Technology         |
|-------------|--------------------|
| Frontend    | React, Tailwind CSS, Axios, Chart.js |
| Backend     | FastAPI (Python), Scikit-learn, Dynamic Programming logic |
| API Gateway | FastAPI (Python), httpx |
| Database    | PostgreSQL         |
| DevOps      | Docker, Docker Compose |
| Others      | REST API, Pydantic, Vite (or CRA) |

---

## 🏗️ Architecture

- **API Gateway** (FastAPI): Central entry point, routes requests to backend microservices.
- **Backend Microservice** (FastAPI): Handles ML predictions, DP logic, and database operations.
- **Frontend** (React): User interface for risk analysis and visualization.
- **Database** (PostgreSQL): Stores risk analysis results and user data.

All services are containerized and orchestrated with Docker Compose.

---

## 🛡️ NVD Vulnerability Management System

Our enhanced NVD integration provides comprehensive vulnerability assessment and enterprise risk management:

### 🔍 **Search & Discovery**
- Real-time vulnerability search using NVD API
- Keyword-based filtering for specific technologies
- Detailed CVE information with publication dates and descriptions

### 📊 **Risk Analysis Dashboard** 
- **Tabbed Interface**: Search, Analysis, and History views
- **Risk Assessment Configuration**: Customizable thresholds (Critical: 80%, High: 60%, Medium: 40%, Low: 20%, Very Low: 10%)
- **Queue Management**: Add specific vulnerabilities to analysis queue
- **Enterprise Metrics**: Comprehensive business impact analysis

### 🏢 **Enterprise Asset Categorization**
- **Web Applications**: React, Vue, Angular, JavaScript, Node.js
- **Infrastructure**: Apache, Nginx, Docker, Kubernetes, Linux, Windows  
- **Databases**: MySQL, PostgreSQL, MongoDB, Redis, Oracle
- **Development Tools**: Git, Jenkins, Python, Java, PHP, Ruby
- **Security Tools**: OpenSSL, SSH, SSL/TLS, Crypto, Vault

### 📈 **Business Impact Analysis**
- Weighted scoring algorithms based on asset criticality
- Automated risk level classification (Critical, High, Medium, Low, Very Low)
- Enterprise-wide risk aggregation and reporting
- Actionable recommendations based on risk assessment

### 🔄 **Queue-Based Processing**
- RabbitMQ integration for asynchronous vulnerability processing
- Selective analysis - only analyze explicitly queued items
- Real-time queue status monitoring
- Bulk analysis capabilities

---

## 📂 Project Structure

```
Quantitative_Risk_Management/
├── backend/
│   └── app/
│       ├── api/          # Routes & Schemas (FastAPI)
│       ├── ml/           # ML models & helpers
│       ├── dp/           # Dynamic programming engine
│       ├── database/     # CRUD & ORM models
│       └── main.py       # FastAPI entry point
├── frontend/
│   └── src/
│       ├── components/   # Reusable UI
│       ├── pages/        # Views
│       ├── services/     # API calls
│       └── App.jsx
├── api_gateway/
│   └── api_gateway.py    # FastAPI API Gateway for microservices
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/your-username/quantitative_risk_managment.git
cd quantitative_risk_managment
```

### 2. Run with Docker

```bash
docker-compose up --build
```

This will start:
- `frontend` on [http://localhost:5173](http://localhost:5173)
- `gateway` (API Gateway) on [http://localhost:8080](http://localhost:8080)
- `backend` on [http://localhost:8000](http://localhost:8000)
- `PostgreSQL` on port 5432

---

## 🧠 How It Works

1. The **API Gateway** (FastAPI) receives all requests from the frontend and routes them to the appropriate backend microservice (risk prediction, NVD, etc.).
2. The **Backend** (FastAPI) exposes endpoints for ML predictions (CICIDS, LANL), dynamic programming, and database operations.
3. The **ML engine** predicts the probability and severity of a risk based on input features.
4. The **DP optimizer** calculates the best mitigation strategy under constraints like budget and impact.
5. Results are visualized and stored in the database.
6. Users interact with predictions and optimizations via the React dashboard.

---

## 🏛️ Design Patterns Used

- **Factory Method:** Used in `ml/engine.py` (`PredictionFactory`) to instantiate the correct prediction strategy (CICIDS, LANL) based on input.
- **Strategy:** Abstract base class `PredictionStrategy` allows interchangeable prediction logic for different models.
- **Singleton:** Each model strategy (`CICIDSPredictionStrategy`, `LANLPredictionStrategy`) is loaded only once per process, ensuring efficient resource use.

---

## ⚙️ Configuration Management

- All secrets and configuration (database URL, API keys, model paths, queue settings) are managed via environment variables and `backend/app/config.py`.
- No secrets or credentials are hardcoded in the codebase.

---

## 🩺 Observability & Health Checks

- Logging is enabled throughout the backend for model loading, errors, and queue operations.
- All prediction endpoints include error handling and log failures.
- `/health` endpoint is available for health checks.

---

## 📨 Message Queue Integration

- The backend integrates a message queue (stub in `backend/app/queue.py`) for asynchronous processing (e.g., logging predictions, batch tasks).
- Ready for Azure Service Bus or a local alternative (see `QUEUE_CONNECTION_STRING` and `QUEUE_NAME` in config).
- Example: Combined prediction results are sent to the queue for async processing.

---

## 🔒 Security & Best Practices

- All code, comments, and documentation are in English.
- Modular, testable, and extensible backend using dependency injection and design patterns.
- No sensitive data in source code or Docker images.

---

## 🌐 National Vulnerability Database (NVD) API Integration

This project integrates with the [National Vulnerability Database (NVD)](https://nvd.nist.gov/) API, provided by the U.S. National Institute of Standards and Technology (NIST).

> The NVD is the U.S. government repository of standards-based vulnerability management data, enabling automation of vulnerability management, security measurement, and compliance.  
> The NVD includes databases of security checklist references, software flaws, product names, and impact metrics, and enriches CVEs with additional metadata such as CVSS scores, CWE, and CPE applicability statements.

- **API Documentation:** [NVD API](https://nvd.nist.gov/developers/vulnerabilities)
- **Legal Disclaimer:** The NVD is a product of the NIST Computer Security Division, Information Technology Laboratory. The NVD does not actively perform vulnerability testing, relying on vendors, third-party security researchers, and vulnerability coordinators to provide information.
- **Credits:**  
  - National Vulnerability Database (NVD), Information Technology Laboratory, NIST  
  - [NVD Legal Disclaimer](https://nvd.nist.gov/general/disclaimer)

---

## 🛣️ API Gateway Endpoints

All frontend requests are routed through the API Gateway. Main endpoints:

| Method | Endpoint                    | Description                           |
|--------|-----------------------------|---------------------------------------|
| POST   | /predict/cicids/            | Predict risk using CICIDS model       |
| POST   | /predict/lanl/              | Predict risk using LANL model         |
| POST   | /predict/combined/          | Combined risk prediction              |
| GET    | /nvd                        | Search NVD vulnerabilities            |
| POST   | /nvd/add_to_queue          | Add keyword to analysis queue         |
| POST   | /nvd/analyze_risk          | Analyze queued vulnerabilities        |
| POST   | /nvd/enterprise_metrics    | Get enterprise risk metrics           |
| GET    | /nvd/queue_status          | Get current queue status              |
| POST   | /nvd/clear_queue           | Clear analysis queue                  |
| GET    | /health                     | Health check                          |

---

## 🌐 API Gateway & CORS

- The API Gateway (FastAPI) is the single entry point for all frontend API calls.
- CORS is enabled to allow requests from the frontend (see `main.py` in `api_gateway`).
- Set your frontend API base URL to the gateway:
  
  ```env
  VITE_API_URL=http://localhost:8080
  ```

---

## 🧠 Model Files & Configuration

- Trained model files must be present in `backend/app/ml/`:
  - `rf_cicids2017_model.pkl`
  - `isolation_forest_model.pkl`
- The backend expects these files at `/app/ml/` inside the Docker container.
- You can override the paths with environment variables `CICIDS_MODEL_PATH` and `LANL_MODEL_PATH` if needed.

---

## ⚙️ Environment Variables Example

```env
# .env for frontend
VITE_API_URL=http://localhost:8080

# docker-compose.yml for backend/gateway
DATABASE_URL=postgresql://postgres:postgres@db:5432/postgres
NVD_API_KEY=your-nvd-api-key
CICIDS_MODEL_PATH=/app/ml/rf_cicids2017_model.pkl
LANL_MODEL_PATH=/app/ml/isolation_forest_model.pkl
```

---

## 🛠️ Troubleshooting

- **CORS/Preflight errors:** Ensure CORS middleware is enabled in the API Gateway (`main.py`).
- **Model file not found:** Make sure model files exist in `backend/app/ml/` and are copied into the Docker image.
- **Import errors:** Remove any local files that shadow standard library modules (e.g., `queue.py`).
- **Frontend 404 on /nvd:** Do not visit `/nvd` directly in the browser; use the app navigation.

---

## 🔄 Development & Hot Reload

- For local development, you can run each service separately and use `docker-compose` for orchestration.
- Rebuild containers after changing dependencies or model paths:
  
  ```sh
  docker-compose build
  docker-compose up -d
  ```

---

## 🆕 Recent Improvements (2025)

### 🛡️ **Enhanced NVD Vulnerability Management**
- **Tabbed Interface**: Complete redesign with Search, Analysis, and History tabs
- **Enterprise Asset Risk Matrix**: Comprehensive risk assessment with business impact analysis
- **Selective Queue Processing**: Only analyze vulnerabilities explicitly added to queue
- **Risk Threshold Configuration**: Customizable risk appetite settings (Critical, High, Medium, Low, Very Low)
- **Analysis History**: Track and audit all risk assessments for compliance

### 🏢 **Enterprise-Level Features**
- **Asset Categorization**: Automatic classification of assets by type (Web Apps, Infrastructure, Databases, Dev Tools, Security)
- **Business Impact Scoring**: Weighted algorithms for calculating enterprise-wide risk exposure
- **Automated Recommendations**: AI-driven suggestions based on risk assessment results
- **Comprehensive Reporting**: Enterprise metrics with drill-down capabilities

### 🎨 **Modern UI/UX Enhancements**
- **Responsive Design**: Full-screen layout that adapts to all screen sizes
- **Centered Layout**: Professional appearance with optimal content distribution
- **Interactive Components**: Custom SVG pie charts and real-time data visualization
- **Improved Navigation**: Intuitive tabbed interface with clear visual hierarchy

### 🔄 **Backend Architecture Improvements**
- **RabbitMQ Integration**: Real message queue for NVD vulnerability searches with reliable async processing
- **Robust Dockerization**: All services (backend, gateway, frontend, RabbitMQ, PostgreSQL) fully containerized
- **API Gateway Enhancement**: Complete endpoint coverage with dependency injection and service abstraction
- **Queue Management**: Lazy connection with retry logic, preventing crashes when RabbitMQ is not ready

### 🐳 **DevOps & Infrastructure**
- **Docker Optimization**: Improved Dockerfiles with proper PYTHONPATH and dependency management
- **CORS Configuration**: Seamless frontend-backend communication through API gateway
- **Error Handling**: Enhanced error handling for queue connections and API routing
- **Health Monitoring**: Comprehensive logging and health check endpoints

### 🔧 **Technical Debt Resolution**
- **Import Standardization**: All backend imports standardized to avoid Docker ModuleNotFoundError
- **State Synchronization**: Frontend state properly synced with backend queue operations
- **Code Quality**: Improved error handling, logging, and code organization
- **Security**: No hardcoded credentials, all configuration via environment variables

---

## 👨‍💻 Author

**Stefan Jativa** — [@byPronox](https://github.com/byPronox)  
*Machine Learning Enthusiast | Software Engineer*

---

## 📄 License

MIT License © 2025 Stefan Jativa

---

## 📚 References & Credits

### LANL Authentication Dataset

- **Source:** [Los Alamos National Laboratory Authentication Data](https://csr.lanl.gov/data/auth/)
- **License:** CC0 — To the extent possible under law, Los Alamos National Laboratory has waived all copyright and related or neighboring rights to User-Computer Authentication Associations in Time. This work is published from: United States.
- **Citing:**
  - A. Hagberg, A. Kent, N. Lemons, and J. Neil, “Credential hopping in authentication graphs,” in 2014 International Conference on Signal-Image Technology Internet-Based Systems (SITIS). IEEE Computer Society, Nov. 2014.
  - A. D. Kent, “User-computer authentication associations in time,” Los Alamos National Laboratory, http://dx.doi.org/10.11578/1160076, 2014.

### CICIDS2017 Dataset

- **Source:** [CICIDS2017 Intrusion Detection Evaluation Dataset](https://www.unb.ca/cic/datasets/ids-2017.html)
- **License:** The CICIDS2017 dataset is publicly available for research purposes.
- **Citing:**
  - Iman Sharafaldin, Arash Habibi Lashkari, and Ali A. Ghorbani, “Toward Generating a New Intrusion Detection Dataset and Intrusion Traffic Characterization”, 4th International Conference on Information Systems Security and Privacy (ICISSP), Portugal, January 2018.

---

*All dataset assets and samples used in this project are credited to their respective authors and institutions as referenced above.*