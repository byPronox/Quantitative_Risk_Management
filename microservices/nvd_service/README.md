# 🛡️ NVD Vulnerability Service

Microservicio para integración con la **National Vulnerability Database (NVD)** del NIST, búsqueda de CVEs y análisis de riesgos empresariales.

## 🏗️ Arquitectura

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│   Backend   │ ──── │ NVD Service │ ──── │   NVD API   │
│   (Proxy)   │ HTTP │  (FastAPI)  │ REST │   (NIST)    │
└─────────────┘      └──────┬──────┘      └─────────────┘
                            │
                            ▼
                     ┌─────────────┐
                     │  PostgreSQL │
                     │  (Supabase) │
                     └─────────────┘
```

## ✨ Características

- **Búsqueda de CVEs** por keyword, producto o vendor
- **Análisis de riesgos** con puntuación CVSS
- **Métricas empresariales** agregadas
- **Categorización de activos** (Web, Infra, DB, DevTools, Security)
- **Cola de análisis** para procesamiento batch
- **Rate limiting** respetando límites de NVD API

## 📦 Tecnologías

| Tecnología | Uso |
|------------|-----|
| Python 3.11 | Runtime |
| FastAPI | API REST |
| httpx | Cliente HTTP async |
| SQLAlchemy | ORM |
| Pydantic | Validación |

## 🚀 Quick Start

### Docker
```bash
docker build -t nvd-service .
docker run -p 8002:8002 --env-file .env nvd-service
```

### Desarrollo Local
```bash
pip install -r requirements.txt
uvicorn src.main:app --host 0.0.0.0 --port 8002 --reload
```

## 🔧 Configuración

### Variables de Entorno

```env
# Server
PORT=8002

# Database (Supabase)
DATABASE_URL=postgresql://postgres:password@db.xxx.supabase.co:5432/postgres

# NVD API
NVD_API_KEY=your-nvd-api-key

# RabbitMQ (opcional)
RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/
```

## 📡 API Endpoints

### GET /nvd
Buscar vulnerabilidades por keyword.

**Query Parameters:**
- `keyword` (required): Término de búsqueda
- `limit` (optional): Máximo resultados (default: 20)

**Response:**
```json
{
  "keyword": "apache",
  "total": 150,
  "vulnerabilities": [
    {
      "cve_id": "CVE-2024-12345",
      "description": "Apache HTTP Server vulnerability...",
      "cvss_score": 7.5,
      "severity": "HIGH",
      "published_date": "2024-01-15"
    }
  ]
}
```

### POST /nvd/add_to_queue
Agregar CVE a la cola de análisis.

```json
{
  "cve_id": "CVE-2024-12345",
  "keyword": "apache"
}
```

### POST /nvd/analyze_risk
Analizar vulnerabilidades en cola.

**Response:**
```json
{
  "analyzed": 5,
  "risk_score": 72.5,
  "risk_level": "HIGH",
  "recommendations": [
    "Update Apache to latest version",
    "Apply security patches"
  ]
}
```

### POST /nvd/enterprise_metrics
Obtener métricas de riesgo empresarial.

**Response:**
```json
{
  "total_assets": 50,
  "total_vulnerabilities": 120,
  "critical_count": 5,
  "high_count": 25,
  "medium_count": 45,
  "low_count": 45,
  "average_cvss": 5.8,
  "risk_by_category": {
    "web_applications": 35,
    "infrastructure": 40,
    "databases": 20,
    "development_tools": 15,
    "security_tools": 10
  }
}
```

### GET /nvd/queue_status
Estado actual de la cola.

### POST /nvd/clear_queue
Limpiar cola de análisis.

### GET /health
Health check del servicio.

## 🏢 Categorías de Activos

| Categoría | Keywords |
|-----------|----------|
| Web Applications | react, vue, angular, javascript, node |
| Infrastructure | apache, nginx, docker, kubernetes, linux |
| Databases | mysql, postgresql, mongodb, redis, oracle |
| Development Tools | git, jenkins, python, java, php |
| Security Tools | openssl, ssh, ssl, crypto, vault |

## 📊 Niveles de Riesgo

| Nivel | CVSS Score | Umbral |
|-------|------------|--------|
| CRITICAL | 9.0 - 10.0 | 80% |
| HIGH | 7.0 - 8.9 | 60% |
| MEDIUM | 4.0 - 6.9 | 40% |
| LOW | 0.1 - 3.9 | 20% |
| VERY LOW | 0.0 | 10% |

## 🐳 Docker

### Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

ENV PYTHONPATH=/app/src
EXPOSE 8002

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]
```

## 🔗 NVD API

Este servicio usa la API oficial del NIST:
- **Documentación:** https://nvd.nist.gov/developers/vulnerabilities
- **Rate Limit:** 5 requests/30 segundos (sin API key)
- **Con API Key:** 50 requests/30 segundos

### Obtener API Key
1. Visitar https://nvd.nist.gov/developers/request-an-api-key
2. Completar formulario
3. Agregar key en `.env`

---

## 📄 Licencia

MIT License © 2025
