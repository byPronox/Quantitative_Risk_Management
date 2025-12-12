# 🔍 NMAP Scanner Service

Microservicio de escaneo de red usando **Nmap**, construido con **Node.js/Express**, integrado con **RabbitMQ** para procesamiento asíncrono y **PostgreSQL/Supabase** para persistencia.

## 🏗️ Arquitectura

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│   Backend   │ ──── │  RabbitMQ   │ ──── │ NMAP Worker │
│   (FastAPI) │ POST │  (Queue)    │ CONSUME │ (Node.js) │
└─────────────┘      └─────────────┘      └──────┬──────┘
                                                  │
                                                  ▼
                                          ┌─────────────┐
                                          │  PostgreSQL │
                                          │  (Supabase) │
                                          └─────────────┘
```

## ✨ Características

- **Escaneo Nmap** con scripts de vulnerabilidades
- **Procesamiento asíncrono** via RabbitMQ
- **Persistencia** en PostgreSQL/Supabase
- **API REST** para consultas directas
- **Rate Limiting** y seguridad con Helmet.js
- **Reconexión automática** a RabbitMQ con exponential backoff
- **SSL/TLS** para conexiones cloud

## 📦 Tecnologías

| Tecnología | Uso |
|------------|-----|
| Node.js 20 | Runtime |
| Express 4.x | API REST |
| amqplib | Cliente RabbitMQ |
| pg | Cliente PostgreSQL |
| xml2js | Parser XML de Nmap |
| Helmet.js | Seguridad HTTP |

## 🚀 Quick Start

### Docker (Recomendado)
```bash
docker build -t nmap-scanner-service .
docker run -p 8004:8004 --env-file .env nmap-scanner-service
```

### Desarrollo Local
```bash
# Instalar nmap
sudo apt-get install nmap nmap-scripts  # Ubuntu/Debian
brew install nmap                        # macOS

# Instalar dependencias
npm install

# Iniciar
npm start
```

## 🔧 Configuración

### Variables de Entorno

```env
# Server
PORT=8004
NODE_ENV=production

# Database (Supabase)
DATABASE_URL=postgresql://postgres:password@db.xxx.supabase.co:5432/postgres

# RabbitMQ
RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/

# Production (CloudAMQP)
# RABBITMQ_URL=amqps://user:pass@host.rmq.cloudamqp.com/vhost
```

## 📡 API Endpoints

### POST /api/v1/scan
Escaneo directo (síncrono).

**Request:**
```json
{
  "ip": "192.168.1.1"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "ip": "192.168.1.1",
    "os": "Linux",
    "status": "up",
    "services": [
      {
        "port": "22",
        "protocol": "tcp",
        "state": "open",
        "name": "ssh",
        "product": "OpenSSH",
        "version": "8.2"
      }
    ],
    "vulnerabilities": [],
    "timestamp": "2025-01-02T21:23:14.694Z"
  }
}
```

### GET /api/v1/health
Health check del servicio.

```json
{
  "status": "healthy",
  "service": "nmap-scanner",
  "uptime": 3600
}
```

### GET /api/v1/test
Verificar instalación de Nmap.

### GET /api/v1/scripts
Listar scripts de vulnerabilidades disponibles.

### GET /api/v1/status
Estado del servicio y conexiones.

## 🐰 RabbitMQ Consumer

El servicio consume jobs de la cola `nmap_scan_queue`:

### Mensaje de Entrada
```json
{
  "job_id": "nmap_abc123",
  "target": "192.168.1.1"
}
```

### Flujo
1. **Recibe** mensaje de la cola
2. **Ejecuta** `nmap -sV --script vuln <target> -oX -`
3. **Parsea** salida XML
4. **Guarda** resultado en PostgreSQL
5. **ACK** el mensaje

### Reconexión
```javascript
// Exponential backoff para reconexión
const delays = [1000, 2000, 4000, 8000, 16000, 30000];
```

## 🐘 Base de Datos

### Tabla `nmap_jobs`

```sql
CREATE TABLE nmap_jobs (
  id SERIAL PRIMARY KEY,
  job_id VARCHAR(50) UNIQUE NOT NULL,
  target VARCHAR(255) NOT NULL,
  status VARCHAR(50) DEFAULT 'queued',
  result JSONB,
  error TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  completed_at TIMESTAMPTZ
);
```

### Estados del Job
| Estado | Descripción |
|--------|-------------|
| `queued` | En cola, esperando procesamiento |
| `processing` | Escaneo en progreso |
| `completed` | Finalizado exitosamente |
| `failed` | Error durante el escaneo |

## 🐳 Docker

### Dockerfile
```dockerfile
FROM node:20-alpine

# Instalar nmap
RUN apk add --no-cache nmap nmap-scripts

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

COPY src/ ./src/

EXPOSE 8004
CMD ["node", "src/index.js"]
```

### Healthcheck
```yaml
healthcheck:
  test: ["CMD", "wget", "-q", "--spider", "http://localhost:8004/api/v1/health"]
  interval: 30s
  timeout: 10s
  retries: 3
```

## 🔒 Seguridad

- **Helmet.js** para headers de seguridad
- **Rate Limiting** para prevenir abuso
- **Validación de IP** antes del escaneo
- **SSL/TLS** para conexiones a base de datos cloud
- **Sin ejecución de comandos arbitrarios**

## 📊 Estructura del Proyecto

```
nmap_scanner/
├── src/
│   ├── index.js       # Entry point + Express API
│   ├── consumer.js    # RabbitMQ consumer
│   ├── scanner.js     # Lógica de escaneo Nmap
│   └── db.js          # Cliente PostgreSQL
├── package.json
├── Dockerfile
└── .env
```

## 🧪 Testing

```bash
# Test de conexión
curl http://localhost:8004/api/v1/health

# Test de escaneo
curl -X POST http://localhost:8004/api/v1/scan \
  -H "Content-Type: application/json" \
  -d '{"ip": "scanme.nmap.org"}'
```

## 📝 Logs

```
[CONSUMER] Starting NMAP Scanner Consumer...
[CONSUMER] Connected to RabbitMQ
[CONSUMER] Waiting for messages in queue: nmap_scan_queue
[CONSUMER] Received job: nmap_abc123 for target: 192.168.1.1
[CONSUMER] Scan completed for job: nmap_abc123
[CONSUMER] Result saved to database
```

---

## 📄 Licencia

MIT License © 2025
