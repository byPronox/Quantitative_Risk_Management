# Configuración de Kong Gateway para Nmap Scanner Service

## ¿Necesitas configurar Kong para Nmap Scanner?

**Respuesta Corta**: **NO es necesario** para el flujo asíncrono de RabbitMQ.

**Respuesta Larga**: Depende de tu arquitectura de despliegue.

---

## Escenarios de Uso

### Escenario 1: Desarrollo Local (Docker Compose) ✅ **NO necesitas Kong**

**Arquitectura Actual**:
```
Frontend (localhost:5173)
    ↓
Backend API Gateway (localhost:8000)
    ↓
Nmap Scanner Service (localhost:8004)
    ↓
RabbitMQ (CloudAMQP)
    ↓
Supabase
```

**Razón**: El API Gateway (backend) ya hace proxy directo al servicio Nmap.

**Configuración**: Ya está implementada en `backend/src/controllers/gateway_controller.py`

---

### Escenario 2: Producción con Kong Gateway ⚠️ **SÍ necesitas Kong**

Si despliegas en producción y quieres usar Kong como punto de entrada único:

**Arquitectura con Kong**:
```
Frontend (https://tu-dominio.com)
    ↓
Kong Gateway (https://kong-6abab64110usqnlwd.kongcloud.dev)
    ↓
Backend API Gateway (interno)
    ↓
Nmap Scanner Service (interno)
```

**Ventajas de usar Kong**:
- ✅ Rate limiting global
- ✅ Autenticación centralizada (API keys, JWT)
- ✅ Caching distribuido
- ✅ Monitoreo y analytics
- ✅ SSL/TLS termination

---

## Configuración de Kong (Si decides usarlo)

### Paso 1: Crear Service en Kong

```bash
# Via Kong Admin API
curl -X POST https://us.api.konghq.com/v2/control-planes/4a89c2c2-c17e-4fb1-b024-6b7b511a8536/core-entities/services \
  -H "Authorization: Bearer kpat_uHDMjKLRj1neIZIBbsW3d2mahGt1LJfGYLylNkloRCfQjjJbM" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "nmap-scanner-service",
    "url": "http://nmap-scanner-service:8004"
  }'
```

### Paso 2: Crear Routes en Kong

#### Route 1: Queue Operations
```bash
curl -X POST https://us.api.konghq.com/v2/control-planes/4a89c2c2-c17e-4fb1-b024-6b7b511a8536/core-entities/services/nmap-scanner-service/routes \
  -H "Authorization: Bearer kpat_uHDMjKLRj1neIZIBbsW3d2mahGt1LJfGYLylNkloRCfQjjJbM" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "nmap-queue-operations",
    "paths": ["/nmap/queue"],
    "strip_path": false,
    "methods": ["GET", "POST"]
  }'
```

#### Route 2: Database Operations
```bash
curl -X POST https://us.api.konghq.com/v2/control-planes/4a89c2c2-c17e-4fb1-b024-6b7b511a8536/core-entities/services/nmap-scanner-service/routes \
  -H "Authorization: Bearer kpat_uHDMjKLRj1neIZIBbsW3d2mahGt1LJfGYLylNkloRCfQjjJbM" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "nmap-database-operations",
    "paths": ["/nmap/database"],
    "strip_path": false,
    "methods": ["GET"]
  }'
```

### Paso 3: Agregar Plugins (Opcional)

#### Rate Limiting
```bash
curl -X POST https://us.api.konghq.com/v2/control-planes/4a89c2c2-c17e-4fb1-b024-6b7b511a8536/core-entities/services/nmap-scanner-service/plugins \
  -H "Authorization: Bearer kpat_uHDMjKLRj1neIZIBbsW3d2mahGt1LJfGYLylNkloRCfQjjJbM" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "rate-limiting",
    "config": {
      "minute": 60,
      "hour": 1000,
      "policy": "local"
    }
  }'
```

#### CORS
```bash
curl -X POST https://us.api.konghq.com/v2/control-planes/4a89c2c2-c17e-4fb1-b024-6b7b511a8536/core-entities/services/nmap-scanner-service/plugins \
  -H "Authorization: Bearer kpat_uHDMjKLRj1neIZIBbsW3d2mahGt1LJfGYLylNkloRCfQjjJbM" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "cors",
    "config": {
      "origins": ["*"],
      "methods": ["GET", "POST"],
      "headers": ["Accept", "Content-Type", "Authorization"],
      "exposed_headers": ["X-Auth-Token"],
      "credentials": true,
      "max_age": 3600
    }
  }'
```

---

## Recomendación para tu Proyecto

### Para Desarrollo Local: **NO uses Kong**

**Razones**:
1. El API Gateway (backend) ya hace proxy
2. Menor complejidad
3. Más rápido para desarrollo
4. No necesitas rate limiting en local

**Configuración Actual** (ya implementada):
```javascript
// Frontend llama a:
http://localhost:8000/api/v1/nmap/queue/job

// Backend proxy a:
http://nmap-scanner-service:8004/api/v1/queue/job
```

### Para Producción: **Considera usar Kong**

**Razones**:
1. Seguridad centralizada
2. Rate limiting para evitar abuso
3. Monitoreo y analytics
4. SSL/TLS termination

**Configuración con Kong**:
```javascript
// Frontend llama a:
https://kong-6abab64110usqnlwd.kongcloud.dev/nmap/queue/job

// Kong proxy a:
http://backend:8000/api/v1/nmap/queue/job

// Backend proxy a:
http://nmap-scanner-service:8004/api/v1/queue/job
```

---

## Resumen

| Aspecto | Sin Kong (Actual) | Con Kong (Producción) |
|---------|-------------------|----------------------|
| **Complejidad** | Baja ✅ | Media |
| **Seguridad** | Media | Alta ✅ |
| **Rate Limiting** | Manual | Automático ✅ |
| **Monitoreo** | Logs básicos | Analytics ✅ |
| **Costo** | Gratis | Kong Konnect (pago) |
| **Recomendado para** | Desarrollo, MVP | Producción |

---

## Conclusión

**Para tu caso actual (desarrollo local con Docker Compose)**:
- ❌ **NO necesitas configurar Kong para Nmap Scanner**
- ✅ El API Gateway (backend) ya maneja el proxy
- ✅ RabbitMQ funciona independientemente de Kong
- ✅ Supabase se conecta directamente desde los servicios

**Si decides usar Kong en el futuro**:
- Sigue los pasos de configuración arriba
- Actualiza `VITE_API_URL` en `.env` para apuntar a Kong
- Agrega autenticación (API keys o JWT)

---

## Verificación

### Sin Kong (Actual)
```bash
# Test directo al backend
curl http://localhost:8000/api/v1/nmap/queue/status

# Debe retornar: {"queue_size": 0, "status": "healthy", ...}
```

### Con Kong (Si lo configuras)
```bash
# Test a través de Kong
curl https://kong-6abab64110usqnlwd.kongcloud.dev/nmap/queue/status

# Debe retornar lo mismo
```
