# 📋 Nomenclatura y Arquitectura del Sistema QRMS

Documento de referencia sobre la nomenclatura, decisiones de diseño y arquitectura del **Quantitative Risk Management System**.

---

## 🏗️ Arquitectura General

### ¿Por qué "QRMS"?

| Término | Significado |
|---------|-------------|
| **Q**uantitative | Métodos numéricos y estadísticos para evaluar riesgos |
| **R**isk | Dominio principal - identificación y evaluación de riesgos |
| **M**anagement | Proceso completo de gestión, no solo detección |
| **S**ystem | Sistema integrado de componentes |

---

## 🐳 Contenedores Docker

### 1. `kong` (API Gateway)

| Aspecto | Descripción |
|---------|-------------|
| **Nombre** | kong |
| **Razón** | API Gateway empresarial estándar de la industria |
| **Función Técnica** | Routing, rate limiting, CORS, load balancing |
| **Función General** | "Recepcionista" que dirige tráfico a servicios internos |
| **Puerto** | 8080 (proxy), 8081 (admin) |
| **Tecnología** | Kong Konnect (Cloud Managed) |

**Configuración:** Gestionado en [cloud.konghq.com](https://cloud.konghq.com). Variables en `.env`.
```yaml
services:
  - name: backend-api
    url: http://backend:8000
    routes:
      - paths: ["/api/v1"]
```

---

### 2. `backend` (API Principal)

| Aspecto | Descripción |
|---------|-------------|
| **Nombre** | backend |
| **Razón** | Convención universal en desarrollo full-stack |
| **Función Técnica** | Auth JWT, proxy a microservicios, lógica de negocio |
| **Función General** | "Cerebro" del sistema - coordina todo |
| **Puerto** | 8000 |
| **Tecnología** | FastAPI, SQLAlchemy, Pydantic |

**Responsabilidades:**
- Autenticación JWT (login, registro, verificación)
- Proxy a microservicios ML, NVD, NMAP
- Publicación de jobs a RabbitMQ
- Gestión de base de datos

---

### 3. `frontend` (Interfaz de Usuario)

| Aspecto | Descripción |
|---------|-------------|
| **Nombre** | frontend |
| **Razón** | Término estándar para capa de presentación web |
| **Función Técnica** | SPA React, consume APIs, visualización |
| **Función General** | "Cara" del sistema - interfaz visual |
| **Puerto** | 5173 |
| **Tecnología** | React 19, Vite, TailwindCSS |

**Páginas:**
- `/login` - Autenticación
- `/` - Dashboard ML
- `/nvd` - Búsqueda de vulnerabilidades
- `/scan` - Escaneo de red
- `/reports` - Reportes

---

### 4. `rabbitmq` (Cola de Mensajes)

| Aspecto | Descripción |
|---------|-------------|
| **Nombre** | rabbitmq |
| **Razón** | Nombre específico de la tecnología usada |
| **Función Técnica** | Broker AMQP, colas de mensajes, pub/sub |
| **Función General** | "Bandeja de tareas" - procesamiento asíncrono |
| **Puerto** | 5672 (AMQP), 15672 (Management UI) |
| **Tecnología** | RabbitMQ 3 Management |

**Colas:**
- `nmap_scan_queue` - Jobs de escaneo Nmap
- `nvd_analysis_queue` - Jobs de análisis NVD

**Producción:** CloudAMQP (SSL/TLS)

---

### 5. `nmap-scanner-service` (Escáner de Red)

| Aspecto | Descripción |
|---------|-------------|
| **Nombre** | nmap-scanner-service |
| **Razón** | Identifica herramienta (nmap) y función (scanner) |
| **Función Técnica** | Escaneo de puertos, detección de servicios, scripts NSE |
| **Función General** | "Detective" - inspecciona servidores |
| **Puerto** | 8004 |
| **Tecnología** | Node.js, Express, Nmap |

**Flujo:**
1. Backend publica job en RabbitMQ
2. Consumer recibe mensaje
3. Ejecuta `nmap -sV --script vuln <target>`
4. Guarda resultado en PostgreSQL

---

### 6. `nvd-service` (Vulnerabilidades)

| Aspecto | Descripción |
|---------|-------------|
| **Nombre** | nvd-service |
| **Razón** | Fuente específica: National Vulnerability Database |
| **Función Técnica** | Proxy a API NVD, búsqueda de CVEs |
| **Función General** | "Bibliotecario" - consulta base de datos de vulnerabilidades |
| **Puerto** | 8002 |
| **Tecnología** | FastAPI, httpx |

---

### 7. `ml-prediction-service` (Machine Learning)

| Aspecto | Descripción |
|---------|-------------|
| **Nombre** | ml-prediction-service |
| **Razón** | ML (Machine Learning) + Prediction describe función exacta |
| **Función Técnica** | Inferencia de modelos, clasificación, detección de anomalías |
| **Función General** | "Analista" - predice riesgos basado en patrones |
| **Puerto** | 8001 |
| **Tecnología** | FastAPI, Scikit-learn, Pandas |

**Modelos:**
- CICIDS2017 (Random Forest) - Detección de intrusiones
- LANL (Isolation Forest) - Anomalías de autenticación

---

## 🗄️ Base de Datos

### Supabase (PostgreSQL Cloud)

| Tabla | Descripción |
|-------|-------------|
| `users` | Usuarios del sistema (auth) |
| `risk_analyses` | Análisis de riesgo realizados |
| `assets` | Activos registrados |
| `vulnerabilities` | CVEs encontradas |
| `nmap_jobs` | Jobs de escaneo Nmap |
| `nvd_jobs` | Jobs de análisis NVD |

**Conexión:** SSL requerido para cloud

---

## 📁 Estructura de Directorios

```
Quantitative_Risk_Management/
├── backend/                    # API Principal
│   └── src/                   # Código fuente (FastAPI convention)
│       ├── config/            # Configuración
│       ├── controllers/       # Endpoints
│       ├── models/            # Modelos de datos
│       ├── services/          # Lógica de negocio
│       └── repositories/      # Acceso a datos
│
├── frontend/                   # UI
│   └── src/                   # Código fuente (React/Vite convention)
│       ├── components/        # Componentes reutilizables
│       ├── pages/             # Páginas/rutas
│       ├── context/           # React Context
│       └── services/          # Llamadas API
│
├── microservices/             # Servicios independientes
│   ├── ml_prediction_service/ # ML
│   ├── nmap_scanner/          # Nmap
│   └── nvd_service/           # NVD
│
├── docker-compose.yml         # Orquestación
├── kong.yml                   # Config Kong Gateway
└── .env                       # Variables de entorno
```

### ¿Por qué `src/` vs `app/`?

| Directorio | Uso | Convención |
|------------|-----|------------|
| `src/` | Frontend, Node.js | React/Vite, npm ecosystem |
| `src/` | Backend Python | Adoptado para consistencia |
| `app/` | (legacy) | FastAPI original, migrado a src/ |

---

## 🔗 Endpoints API

### Autenticación
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/v1/auth/login` | Login JWT |
| GET | `/api/v1/auth/me` | Usuario actual |
| POST | `/api/v1/auth/verify` | Verificar token |

### Escaneo
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/v1/nmap/scan` | Iniciar escaneo |
| GET | `/api/v1/nmap/job/{id}` | Estado del job |

### Vulnerabilidades
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/v1/nvd/search` | Buscar CVEs |
| POST | `/api/v1/nvd/analyze` | Analizar riesgos |

### ML Prediction
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/v1/predict/cicids` | Predicción CICIDS |
| POST | `/api/v1/predict/lanl` | Predicción LANL |
| POST | `/api/v1/predict/combined` | Predicción combinada |

---

## 🎨 Patrones de Diseño

### Strategy Pattern (ML Service)
```python
class PredictionStrategy(ABC):
    @abstractmethod
    def predict(self, features: dict) -> dict:
        pass

class CICIDSStrategy(PredictionStrategy):
    def predict(self, features: dict) -> dict:
        return self.model.predict(features)
```

### Repository Pattern (Backend)
```python
class RiskRepository:
    def get_all(self) -> List[RiskAnalysis]:
        return self.db.query(RiskAnalysis).all()
    
    def create(self, data: dict) -> RiskAnalysis:
        analysis = RiskAnalysis(**data)
        self.db.add(analysis)
        return analysis
```

### Consumer Pattern (Nmap Service)
```javascript
channel.consume('nmap_scan_queue', async (msg) => {
    const job = JSON.parse(msg.content);
    const result = await runNmapScan(job.target);
    await saveResult(job.job_id, result);
    channel.ack(msg);
});
```

---

## 🔒 Seguridad

| Aspecto | Implementación |
|---------|----------------|
| Autenticación | JWT con bcrypt hash |
| CORS | Configurado en Kong |
| Rate Limiting | Kong plugin |
| Secretos | Variables de entorno (.env) |
| SSL/TLS | Conexiones cloud (Supabase, CloudAMQP) |

---

## 📚 Referencias

- **Kong Gateway:** https://docs.konghq.com/
- **FastAPI:** https://fastapi.tiangolo.com/
- **React:** https://react.dev/
- **RabbitMQ:** https://www.rabbitmq.com/documentation.html
- **NVD API:** https://nvd.nist.gov/developers/

---

*Última actualización: Diciembre 2025*
