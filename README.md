# ⚠️ Quantitative Risk Management System

A full-stack, microservices-based application for **quantitative risk assessment and mitigation**, powered by **Machine Learning** and **Dynamic Programming**. This system predicts potential risks, evaluates their impact, and recommends optimal mitigation strategies using intelligent algorithms and data-driven insights.

---

## ✨ Features

- 🎯 Risk Prediction using trained ML models (CICIDS, LANL)
- 🧠 Dynamic Programming engine for optimal decision-making
- 📊 Interactive Dashboard built with React + Tailwind CSS
- 🔄 RESTful APIs powered by FastAPI (Python)
- 🐳 Fully containerized with Docker & Docker Compose
- 📁 PostgreSQL Database integration
- 📈 Data visualization with Chart.js
- 🛡️ Integration with the National Vulnerability Database (NVD) API
- 🏛️ Microservices architecture with API Gateway

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

- **Factory Method:** For loading and instantiating different ML models and encoders.
- **Strategy:** For switching between different prediction algorithms (CICIDS, LANL).
- **Singleton:** For ensuring only one instance of each ML model is loaded in memory.

---

## 🛠️ Future Enhancements

- ✅ Authentication system (JWT)
- ✅ Admin dashboard with analytics
- ✅ Model training from the UI
- ✅ CI/CD pipeline
- ✅ Exportable reports (PDF)

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