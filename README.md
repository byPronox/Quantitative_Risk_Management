
# ⚠️ Quantitative Risk Management System

A full-stack application for **quantitative risk assessment and mitigation**, powered by **Machine Learning** and **Dynamic Programming**. This system predicts potential risks, evaluates their impact, and recommends optimal mitigation strategies using intelligent algorithms and data-driven insights.

---

## ✨ Features

- 🎯 Risk Prediction using trained ML models
- 🧠 Dynamic Programming engine for optimal decision-making
- 📊 Interactive Dashboard built with React + Tailwind CSS
- 🔄 RESTful API powered by FastAPI
- 🐳 Fully containerized with Docker & Docker Compose
- 📁 PostgreSQL Database integration
- 📈 Data visualization with Chart.js

---

## 🧱 Tech Stack

| Layer        | Technology         |
|-------------|--------------------|
| Frontend    | React, Tailwind CSS, Axios, Chart.js |
| Backend     | FastAPI (Python), Scikit-learn, DP logic |
| Database    | PostgreSQL         |
| DevOps      | Docker, Docker Compose |
| Others      | REST API, Pydantic, Vite (or CRA) |

---

## 📂 Project Structure

```
Quantitative_Risk_Management/
├── backend/
│   └── app/
│       ├── api/          # Routes & Schemas
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
- `backend` on [http://localhost:8000](http://localhost:8000)
- `PostgreSQL` on port 5432

---

## 🧠 How It Works

1. The **ML engine** predicts the probability and severity of a risk based on input features.
2. The **DP optimizer** calculates the best mitigation strategy under constraints like budget and impact.
3. Results are visualized and stored in the database.
4. Users can interact with predictions and optimizations via the React dashboard.

---

## 🛠️ Future Enhancements

- ✅ Authentication system (JWT)
- ✅ Admin dashboard with analytics
- ✅ Model training from the UI
- ✅ CI/CD pipeline
- ✅ Exportable reports (PDF)

---

## 👨‍💻 Author

**Stefan Jativa** — [@byPronox](https://github.com/byPronox)  
*Machine Learning Enthusiast | Software Engineer*

---

## 📚 References & Credits

### LANL Authentication Dataset

### LANL Authentication Dataset

- **Source:** [Los Alamos National Laboratory Authentication Data](https://csr.lanl.gov/data/auth/)
- **License:** CC0 — To the extent possible under law, Los Alamos National Laboratory has waived all copyright and related or neighboring rights to User-Computer Authentication Associations in Time. This work is published from: United States.
- **Citing:**
  - A. Hagberg, A. Kent, N. Lemons, and J. Neil, “Credential hopping in authentication graphs,” in 2014 International Conference on Signal-Image Technology Internet-Based Systems (SITIS). IEEE Computer Society, Nov. 2014.
  - A. D. Kent, “User-computer authentication associations in time,” Los Alamos National Laboratory, http://dx.doi.org/10.11578/1160076, 2014.

---

### CICIDS2017 Dataset

- **Source:** [CICIDS2017 Intrusion Detection Evaluation Dataset](https://www.unb.ca/cic/datasets/ids-2017.html)
- **License:** The CICIDS2017 dataset is publicly available for research purposes.
- **Citing:**
  - Iman Sharafaldin, Arash Habibi Lashkari, and Ali A. Ghorbani, “Toward Generating a New Intrusion Detection Dataset and Intrusion Traffic Characterization”, 4th International Conference on Information Systems Security and Privacy (ICISSP), Portugal, January 2018.

---

*All dataset assets and samples used in this project are credited to their respective authors and institutions as referenced above.*

---
## 📄 License

MIT License © 2025 Stefan Jativa
