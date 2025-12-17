# Arquitectura del Sistema Distribuido de Análisis de Vulnerabilidades NVD

## Tabla de Contenidos
1. [Visión General del Sistema Distribuido](#visión-general-del-sistema-distribuido)
2. [Componentes del Sistema](#componentes-del-sistema)
3. [Flujo Completo de Análisis NVD](#flujo-completo-de-análisis-nvd)
4. [Características de Sistema Distribuido](#características-de-sistema-distribuido)
5. [Sincronización de Tiempo Distribuido](#sincronización-de-tiempo-distribuido)
6. [Evidencia y Verificación del Sistema](#evidencia-y-verificación-del-sistema)
7. [Justificación Técnica de Componentes](#justificación-técnica-de-componentes)

---

## Visión General del Sistema Distribuido

Este sistema implementa una **arquitectura de microservicios distribuidos** para el análisis asíncrono de vulnerabilidades utilizando la base de datos NVD (National Vulnerability Database). El sistema cumple con los principios fundamentales de sistemas distribuidos:

### Principios de Sistemas Distribuidos Implementados

1. **Transparencia de Acceso**: Los clientes acceden a servicios remotos como si fueran locales a través del API Gateway
2. **Transparencia de Ubicación**: Los servicios pueden estar en diferentes nodos sin que el cliente lo sepa
3. **Transparencia de Concurrencia**: Múltiples workers pueden procesar trabajos simultáneamente
4. **Transparencia de Replicación**: Los servicios pueden escalarse horizontalmente (réplicas)
5. **Transparencia de Fallos**: El sistema maneja fallos de componentes individuales sin colapsar
6. **Escalabilidad Horizontal**: Capacidad de agregar más workers/servicios según demanda
7. **Desacoplamiento**: Componentes independientes comunicados por mensajería asíncrona
8. **Persistencia Distribuida**: Base de datos centralizada (Supabase) accesible desde todos los nodos

---

## Componentes del Sistema

### 1. Frontend (Cliente Web)
**Tecnología**: React + Vite  
**Puerto**: 5173  
**Rol**: Interfaz de usuario para interactuar con el sistema

**Responsabilidades**:
- Enviar keywords para análisis de vulnerabilidades
- Visualizar estado de trabajos (pending, processing, completed)
- Mostrar resultados de análisis (vulnerabilidades encontradas)
- Controlar el consumidor de cola (start/stop)

**Justificación Técnica**:
- **React**: Framework declarativo que facilita la gestión de estado complejo (trabajos, resultados, estados de carga)
- **Vite**: Build tool moderno con HMR (Hot Module Replacement) para desarrollo ágil
- **SPA (Single Page Application)**: Reduce latencia al evitar recargas completas de página

---

### 2. API Gateway (Backend Principal)
**Tecnología**: FastAPI (Python)  
**Puerto**: 8000  
**Rol**: Punto de entrada único (Single Entry Point) para todas las solicitudes

**Responsabilidades**:
- **Enrutamiento**: Proxy de solicitudes a microservicios específicos
- **Autenticación/Autorización**: Validación de tokens JWT (si aplica)
- **Rate Limiting**: Control de tasa de solicitudes
- **Load Balancing**: Distribución de carga entre réplicas de servicios
- **Circuit Breaker**: Manejo de fallos en servicios downstream

**Justificación Técnica**:
- **FastAPI**: Framework asíncrono de alto rendimiento (basado en Starlette + Pydantic)
- **Async/Await**: Manejo eficiente de I/O no bloqueante para miles de conexiones concurrentes
- **Patrón API Gateway**: Centraliza cross-cutting concerns (logging, monitoring, security)
- **Desacoplamiento**: El frontend no conoce la topología interna de microservicios

**Endpoints Clave**:
```
GET  /api/v1/queue/results/all    → Obtener todos los trabajos
GET  /api/v1/queue/status          → Estado de la cola RabbitMQ
POST /api/v1/queue/job             → Crear nuevo trabajo
POST /api/v1/queue/consumer/start  → Iniciar consumidor
```

---

### 3. NVD Microservice (Producer/Consumer)
**Tecnología**: FastAPI + Pika (RabbitMQ Client)  
**Puerto**: 8002  
**Rol**: Servicio especializado en análisis de vulnerabilidades NVD

**Responsabilidades**:
- **Producer**: Publicar trabajos en RabbitMQ
- **Consumer**: Procesar trabajos de la cola
- **API Integration**: Consultar NVD API (o Kong Gateway)
- **Data Persistence**: Guardar resultados en Supabase

**Justificación Técnica**:
- **Microservicio Especializado**: Single Responsibility Principle (SRP)
- **Pika**: Cliente oficial de RabbitMQ para Python (AMQP 0-9-1)
- **Async Processing**: Evita bloquear el API Gateway en análisis largos
- **Stateless**: No mantiene estado entre requests (facilita escalado horizontal)

**Componentes Internos**:

#### 3.1. Queue Service (`queue_service.py`)
**Responsabilidades**:
- Conexión a RabbitMQ (CloudAMQP)
- Publicación de mensajes (jobs)
- Consumo de mensajes (consumer thread)
- Gestión de ACK/NACK

**Patrón Implementado**: **Producer-Consumer Pattern**

```python
# Publicación (Producer)
def add_job(keyword, metadata):
    1. Generar job_id único
    2. Guardar en Supabase (estado: pending)
    3. Publicar mensaje en RabbitMQ
    4. Retornar job_id al cliente

# Consumo (Consumer)
def start_consumer():
    1. Conectar a RabbitMQ
    2. Declarar cola (durable)
    3. Configurar callback para mensajes
    4. Iniciar consumo en thread separado
```

#### 3.2. NVD Service (`nvd_service.py`)
**Responsabilidades**:
- Consultar NVD API (https://services.nvd.nist.gov/rest/json/cves/2.0)
- Parsear respuestas JSON
- Transformar datos a formato interno
- Manejo de rate limiting (NVD API: 5 requests/30s sin API key)

**Justificación Técnica**:
- **httpx**: Cliente HTTP asíncrono (sucesor de requests)
- **Retry Logic**: Manejo de fallos transitorios (exponential backoff)
- **API Key Support**: Aumenta rate limit a 50 requests/30s

#### 3.3. Database Service (`database_service.py`)
**Responsabilidades**:
- Conexión a Supabase (PostgreSQL)
- CRUD operations en tablas `nvd_jobs` y `nvd_vulnerabilities`
- Transacciones ACID
- Connection pooling

**Justificación Técnica**:
- **asyncpg**: Driver PostgreSQL asíncrono de alto rendimiento
- **Connection Pooling**: Reutilización de conexiones (reduce overhead)
- **Prepared Statements**: Prevención de SQL injection

#### 3.4. Time Service (`time_service.py`)
**Responsabilidades**:
- Sincronización de tiempo distribuido
- Fallback a tiempo local si falla servicio externo

**Patrón Implementado**: **Distributed Time Synchronization**

```python
async def get_current_timestamp():
    try:
        # 1. Intentar WorldTimeAPI (fuente externa confiable)
        response = await httpx.get("http://worldtimeapi.org/api/timezone/Etc/UTC")
        return response.json()["unixtime"]
    except:
        # 2. Fallback: Tiempo del contenedor Docker
        return time.time()
```

**Justificación Técnica**:
- **Consistencia Temporal**: Todos los nodos usan la misma referencia de tiempo
- **Evita Clock Skew**: Diferencias de reloj entre máquinas
- **Crítico para**: Ordenamiento de eventos, TTL de mensajes, auditoría

---

### 4. RabbitMQ (Message Broker)
**Tecnología**: CloudAMQP (RabbitMQ as a Service)  
**Protocolo**: AMQP 0-9-1  
**Rol**: Sistema de mensajería asíncrona

**Responsabilidades**:
- **Message Queuing**: Almacenar trabajos pendientes
- **Delivery Guarantees**: Asegurar entrega de mensajes (durabilidad)
- **Load Balancing**: Distribuir trabajos entre múltiples consumers
- **Dead Letter Queue**: Manejar mensajes fallidos

**Justificación Técnica**:
- **Desacoplamiento Temporal**: Producer y Consumer no necesitan estar activos simultáneamente
- **Buffering**: Absorbe picos de carga (backpressure)
- **Escalabilidad**: Múltiples consumers pueden procesar en paralelo
- **Durabilidad**: Mensajes persisten en disco (sobreviven reinicio del broker)
- **CloudAMQP**: Managed service (alta disponibilidad, backups automáticos)

**Configuración de Cola**:
```python
channel.queue_declare(
    queue='nvd_analysis_queue',
    durable=True,  # Cola persiste reinicio
    arguments={
        'x-message-ttl': 3600000,  # TTL: 1 hora
        'x-max-length': 10000       # Máximo 10k mensajes
    }
)
```

**Propiedades de Mensaje**:
```python
properties = pika.BasicProperties(
    delivery_mode=2,  # Mensaje persistente
    content_type='application/json',
    timestamp=int(time.time())
)
```

---

### 5. Supabase (Base de Datos Distribuida)
**Tecnología**: PostgreSQL (Supabase Cloud)  
**Rol**: Almacenamiento persistente centralizado

**Tablas Principales**:

#### 5.1. `nvd_jobs`
```sql
CREATE TABLE nvd_jobs (
    id SERIAL PRIMARY KEY,
    job_id VARCHAR(255) UNIQUE NOT NULL,
    keyword VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL,  -- pending, processing, completed, failed
    total_results INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    processed_at TIMESTAMP,
    processed_via VARCHAR(50),  -- queue_consumer, direct_api
    vulnerabilities JSONB  -- Array de vulnerabilidades
);
```

#### 5.2. `nvd_vulnerabilities`
```sql
CREATE TABLE nvd_vulnerabilities (
    id SERIAL PRIMARY KEY,
    job_id VARCHAR(255) REFERENCES nvd_jobs(job_id),
    cve_id VARCHAR(50) NOT NULL,
    description TEXT,
    severity VARCHAR(20),
    cvss_score DECIMAL(3,1),
    published_date TIMESTAMP,
    last_modified TIMESTAMP,
    raw_data JSONB  -- Datos completos del CVE
);
```

**Justificación Técnica**:
- **PostgreSQL**: RDBMS ACID-compliant (transacciones, integridad referencial)
- **JSONB**: Almacenamiento eficiente de datos semi-estructurados (vulnerabilidades)
- **Índices**: Búsqueda rápida por job_id, cve_id, keyword
- **Supabase**: Managed PostgreSQL con APIs REST/GraphQL auto-generadas
- **Transaction Pooler**: Conexiones eficientes (puerto 6543)
- **Replicación**: Backups automáticos y alta disponibilidad

**Connection String**:
```
postgresql://postgres.PROJECT:PASSWORD@aws-1-us-east-1.pooler.supabase.com:6543/postgres
```

---

### 6. Kong Gateway (API Gateway Externo - Opcional)
**Tecnología**: Kong Konnect Cloud  
**Rol**: Gateway para NVD API (rate limiting, caching)

**Responsabilidades**:
- **Rate Limiting**: Evitar exceder límites de NVD API
- **Caching**: Reducir llamadas redundantes
- **API Key Management**: Centralizar credenciales
- **Monitoring**: Métricas de uso de API

**Justificación Técnica**:
- **Protección de API Key**: No exponer credenciales en código
- **Caching Distribuido**: Redis backend para cache compartido
- **Circuit Breaker**: Evitar cascading failures si NVD API cae

**Configuración**:
```yaml
KONG_PROXY_URL: https://kong-6abab64110usqnlwd.kongcloud.dev
USE_KONG_NVD: false  # Actualmente deshabilitado (uso directo de NVD API)
```

---

## Flujo Completo de Análisis NVD

### Fase 1: Solicitud de Análisis (Frontend → API Gateway → NVD Service)

```mermaid
sequenceDiagram
    participant F as Frontend
    participant G as API Gateway
    participant N as NVD Service
    participant R as RabbitMQ
    participant S as Supabase
    participant T as TimeService

    F->>G: POST /api/v1/queue/job?keyword=python
    G->>N: POST /api/v1/queue/job?keyword=python
    N->>T: GET current_timestamp()
    T-->>N: 1765978769.481
    N->>S: INSERT INTO nvd_jobs (job_id, keyword, status, created_at)
    S-->>N: OK (job persisted)
    N->>R: PUBLISH message {job_id, keyword, created_at}
    R-->>N: ACK
    N-->>G: {job_id: "1765978769481-1", status: "queued"}
    G-->>F: {job_id: "1765978769481-1", status: "queued"}
```

**Detalles Técnicos**:

1. **Frontend** envía solicitud HTTP POST con keyword
2. **API Gateway** valida request y hace proxy a NVD Service
3. **NVD Service** ejecuta `queue_service.add_job()`:
   - Genera `job_id` único: `timestamp-counter`
   - Obtiene timestamp distribuido de TimeService
   - Persiste job en Supabase con estado `pending`
   - Publica mensaje en RabbitMQ (cola: `nvd_analysis_queue`)
4. **RabbitMQ** almacena mensaje en cola durable
5. **Respuesta** retorna job_id al cliente (operación no bloqueante)

**Ventajas del Patrón Asíncrono**:
- ✅ **Baja Latencia**: Cliente recibe respuesta inmediata (~100ms)
- ✅ **Escalabilidad**: API Gateway no se bloquea esperando análisis largo
- ✅ **Resiliencia**: Si NVD API está lento, no afecta al cliente
- ✅ **Buffering**: Cola absorbe picos de carga

---

### Fase 2: Procesamiento Asíncrono (Consumer → NVD API → Supabase)

```mermaid
sequenceDiagram
    participant C as Consumer Thread
    participant R as RabbitMQ
    participant N as NVD API
    participant S as Supabase
    participant T as TimeService

    C->>R: CONSUME message from queue
    R-->>C: {job_id, keyword, created_at}
    C->>T: GET current_timestamp()
    T-->>C: 1765978800.972
    C->>S: UPDATE nvd_jobs SET status='processing', processed_at=...
    S-->>C: OK
    C->>N: GET /cves?keywordSearch=python&resultsPerPage=100
    N-->>C: {vulnerabilities: [...], totalResults: 1154}
    C->>S: UPDATE nvd_jobs SET status='completed', vulnerabilities=[...]
    C->>S: INSERT INTO nvd_vulnerabilities (job_id, cve_id, ...)
    S-->>C: OK
    C->>R: ACK message
```

**Detalles Técnicos**:

1. **Consumer Thread** (iniciado por `start_consumer()`):
   - Conecta a RabbitMQ con `pika.BlockingConnection`
   - Declara cola (idempotente)
   - Configura callback `on_message_callback`
   - Inicia `channel.start_consuming()` (blocking loop)

2. **Callback de Mensaje**:
   ```python
   def callback(ch, method, properties, body):
       job_data = json.loads(body)
       job_id = job_data['job_id']
       keyword = job_data['keyword']
       
       # 1. Actualizar estado a 'processing'
       update_job_status(job_id, 'processing')
       
       # 2. Consultar NVD API
       vulnerabilities = nvd_service.search_vulnerabilities(keyword)
       
       # 3. Guardar resultados en Supabase
       save_job_results(job_id, vulnerabilities)
       
       # 4. ACK mensaje (confirmar procesamiento)
       ch.basic_ack(method.delivery_tag)
   ```

3. **Consulta a NVD API**:
   ```python
   async def search_vulnerabilities(keyword):
       url = "https://services.nvd.nist.gov/rest/json/cves/2.0"
       params = {
           "keywordSearch": keyword,
           "resultsPerPage": 100
       }
       headers = {"apiKey": NVD_API_KEY} if NVD_API_KEY else {}
       
       response = await httpx.get(url, params=params, headers=headers)
       data = response.json()
       
       return {
           "vulnerabilities": data.get("vulnerabilities", []),
           "totalResults": data.get("totalResults", 0)
       }
   ```

4. **Persistencia en Supabase**:
   - Actualiza `nvd_jobs` con estado `completed`
   - Inserta vulnerabilidades en `nvd_vulnerabilities` (bulk insert)
   - Usa transacción para garantizar atomicidad

5. **ACK de Mensaje**:
   - `ch.basic_ack(delivery_tag)`: Confirma procesamiento exitoso
   - RabbitMQ elimina mensaje de la cola
   - Si falla: `ch.basic_nack(requeue=True)` → mensaje vuelve a la cola

**Manejo de Errores**:
```python
try:
    # Procesamiento
    process_job(job_data)
    ch.basic_ack(method.delivery_tag)
except Exception as e:
    logger.error(f"Error processing job: {e}")
    # NACK sin requeue (evitar loops infinitos)
    ch.basic_nack(method.delivery_tag, requeue=False)
    # Marcar job como 'failed' en Supabase
    update_job_status(job_id, 'failed', error=str(e))
```

---

### Fase 3: Consulta de Resultados (Frontend → API Gateway → Supabase)

```mermaid
sequenceDiagram
    participant F as Frontend
    participant G as API Gateway
    participant N as NVD Service
    participant S as Supabase

    F->>G: GET /api/v1/queue/results/all
    G->>N: GET /api/v1/queue/results/all
    N->>S: SELECT * FROM nvd_jobs ORDER BY created_at DESC
    S-->>N: [{job_id, keyword, status, vulnerabilities}, ...]
    N-->>G: {success: true, jobs: [...]}
    G-->>F: {success: true, jobs: [...]}
    F->>F: Renderizar lista de trabajos
```

**Detalles Técnicos**:

1. **Frontend** hace polling o click en "Actualizar"
2. **API Gateway** proxy a NVD Service
3. **NVD Service** ejecuta `queue_service.get_all_job_results()`:
   ```python
   async def get_all_job_results():
       jobs = await database_service.get_all_jobs()
       return {"success": True, "jobs": jobs}
   ```
4. **Database Service** consulta Supabase:
   ```python
   async def get_all_jobs():
       query = """
           SELECT id, job_id, keyword, status, total_results,
                  created_at, processed_at, processed_via,
                  vulnerabilities
           FROM nvd_jobs
           ORDER BY created_at DESC
           LIMIT 100
       """
       return await conn.fetch(query)
   ```
5. **Frontend** renderiza trabajos con estados:
   - 🟡 **Pending**: En cola, esperando procesamiento
   - 🔵 **Processing**: Siendo procesado por consumer
   - 🟢 **Completed**: Análisis completado, resultados disponibles
   - 🔴 **Failed**: Error en procesamiento

---

## Características de Sistema Distribuido

### 1. Desacoplamiento (Loose Coupling)

**Implementación**:
- **Mensajería Asíncrona**: RabbitMQ desacopla producers de consumers
- **API Gateway**: Frontend no conoce microservicios internos
- **Contratos de API**: Interfaces bien definidas (OpenAPI/Swagger)

**Beneficios**:
- Servicios pueden evolucionar independientemente
- Fallos en un servicio no propagan a otros
- Facilita testing unitario (mocking de dependencias)

---

### 2. Escalabilidad Horizontal

**Implementación**:
```yaml
# docker-compose.yml
nvd-service:
  deploy:
    mode: replicated
    replicas: 3  # 3 instancias del servicio
```

**Estrategia de Escalado**:
- **Stateless Services**: NVD Service no mantiene estado (facilita réplicas)
- **Load Balancing**: RabbitMQ distribuye mensajes entre consumers (round-robin)
- **Database Pooling**: Conexiones compartidas entre réplicas

**Evidencia**:
```bash
# Escalar a 5 réplicas
docker-compose up --scale nvd-service=5

# Verificar réplicas
docker-compose ps
# Salida:
# nvd-service_1  Up
# nvd-service_2  Up
# nvd-service_3  Up
# nvd-service_4  Up
# nvd-service_5  Up
```

---

### 3. Tolerancia a Fallos (Fault Tolerance)

**Mecanismos Implementados**:

#### 3.1. Retry Logic (Reintentos)
```python
@retry(max_attempts=3, backoff=exponential)
async def search_vulnerabilities(keyword):
    # Intenta hasta 3 veces con backoff exponencial
    # 1er intento: inmediato
    # 2do intento: espera 2s
    # 3er intento: espera 4s
    pass
```

#### 3.2. Circuit Breaker
```python
circuit_breaker = CircuitBreaker(
    failure_threshold=5,  # Abre después de 5 fallos
    timeout=60            # Cierra después de 60s
)

@circuit_breaker
async def call_nvd_api():
    # Si falla 5 veces, circuit breaker se abre
    # Requests subsecuentes fallan inmediatamente (fail-fast)
    # Después de 60s, intenta cerrar el circuito
    pass
```

#### 3.3. Message Durability
```python
# Cola durable (persiste reinicio de RabbitMQ)
channel.queue_declare(queue='nvd_analysis_queue', durable=True)

# Mensajes persistentes (persisten reinicio de RabbitMQ)
properties = pika.BasicProperties(delivery_mode=2)
channel.basic_publish(body=message, properties=properties)
```

#### 3.4. Dead Letter Queue (DLQ)
```python
# Mensajes que fallan N veces van a DLQ
channel.queue_declare(
    queue='nvd_analysis_queue',
    arguments={
        'x-dead-letter-exchange': 'dlx',
        'x-dead-letter-routing-key': 'failed_jobs'
    }
)
```

---

### 4. Consistencia Eventual (Eventual Consistency)

**Escenario**:
1. Job se crea en Supabase (estado: `pending`)
2. Mensaje se publica en RabbitMQ
3. Consumer procesa mensaje
4. Resultados se guardan en Supabase (estado: `completed`)

**Ventana de Inconsistencia**:
- Entre paso 1 y 4, el job existe en Supabase pero no tiene resultados
- Frontend puede ver job en estado `pending` o `processing`
- Eventualmente (segundos/minutos), el job alcanza estado `completed`

**Justificación**:
- **CAP Theorem**: Priorizamos Availability y Partition Tolerance sobre Consistency
- **Aceptable para este caso de uso**: Análisis de vulnerabilidades no requiere consistencia fuerte
- **Alternativa (no implementada)**: Transacciones distribuidas (2PC) → mayor latencia y complejidad

---

### 5. Idempotencia

**Definición**: Ejecutar la misma operación múltiples veces produce el mismo resultado

**Implementación**:
```python
async def save_job_results(job_id, vulnerabilities):
    # Usar UPSERT (INSERT ... ON CONFLICT UPDATE)
    query = """
        INSERT INTO nvd_jobs (job_id, keyword, status, vulnerabilities)
        VALUES ($1, $2, $3, $4)
        ON CONFLICT (job_id) DO UPDATE
        SET status = EXCLUDED.status,
            vulnerabilities = EXCLUDED.vulnerabilities,
            processed_at = NOW()
    """
    await conn.execute(query, job_id, keyword, 'completed', vulnerabilities)
```

**Beneficio**:
- Si consumer procesa el mismo mensaje 2 veces (por timeout), no crea duplicados
- Garantiza exactamente-una-vez (exactly-once) semántica a nivel de aplicación

---

## Sincronización de Tiempo Distribuido

### Problema: Clock Skew

En sistemas distribuidos, cada nodo tiene su propio reloj:
- **Servidor A**: 2025-12-17 08:30:00
- **Servidor B**: 2025-12-17 08:29:55 (5 segundos de diferencia)
- **Servidor C**: 2025-12-17 08:30:10 (10 segundos de diferencia)

**Consecuencias**:
- Ordenamiento incorrecto de eventos
- TTL de mensajes inconsistente
- Logs con timestamps confusos

### Solución: Time Service

**Arquitectura**:
```
┌─────────────┐
│ TimeService │
└──────┬──────┘
       │
       ├─── 1. WorldTimeAPI (fuente externa confiable)
       │    └─ http://worldtimeapi.org/api/timezone/Etc/UTC
       │
       └─── 2. Docker Container Time (fallback)
            └─ time.time() del contenedor
```

**Implementación**:
```python
# microservices/nvd_service/src/services/time_service.py

class TimeService:
    @staticmethod
    async def get_current_timestamp() -> float:
        """
        Obtiene timestamp distribuido con fallback.
        
        Returns:
            float: Unix timestamp (segundos desde epoch)
        """
        try:
            # Intento 1: WorldTimeAPI (fuente externa)
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.get(
                    "http://worldtimeapi.org/api/timezone/Etc/UTC"
                )
                response.raise_for_status()
                data = response.json()
                timestamp = data["unixtime"]
                logger.info(f"Using WorldTimeAPI timestamp: {timestamp}")
                return float(timestamp)
        except Exception as e:
            # Intento 2: Tiempo local del contenedor Docker
            logger.warning(f"WorldTimeAPI failed: {e}, using local time")
            timestamp = time.time()
            logger.info(f"Using local Docker time: {timestamp}")
            return timestamp
```

**Uso en el Sistema**:

1. **Creación de Job**:
```python
async def add_job(keyword, metadata):
    # Obtener timestamp distribuido
    created_at = await TimeService.get_current_timestamp()
    
    job = {
        "job_id": f"{int(created_at * 1000)}-{counter}",
        "keyword": keyword,
        "created_at": created_at,  # Timestamp consistente
        "status": "pending"
    }
    await database_service.save_job_results([job])
```

2. **Procesamiento de Job**:
```python
def callback(ch, method, properties, body):
    # Obtener timestamp distribuido para processed_at
    processed_at = asyncio.run(TimeService.get_current_timestamp())
    
    job_update = {
        "job_id": job_id,
        "status": "completed",
        "processed_at": processed_at  # Timestamp consistente
    }
    save_to_database(job_update)
```

**Ventajas**:
- ✅ **Consistencia**: Todos los nodos usan la misma referencia de tiempo
- ✅ **Ordenamiento Correcto**: Eventos se ordenan correctamente por timestamp
- ✅ **Auditoría**: Logs con timestamps precisos
- ✅ **Resiliencia**: Fallback a tiempo local si WorldTimeAPI falla

**Alternativas (no implementadas)**:
- **NTP (Network Time Protocol)**: Requiere configuración a nivel de OS
- **Google TrueTime**: Requiere hardware especializado (GPS + atomic clocks)
- **Logical Clocks (Lamport)**: No proporciona tiempo real, solo ordenamiento causal

---

## Evidencia y Verificación del Sistema

### 1. Verificar Servicios Activos

**Docker Compose**:
```bash
# Listar todos los contenedores
docker-compose ps

# Salida esperada:
# NAME                                    STATUS              PORTS
# backend-1                               Up (healthy)        0.0.0.0:8000->8000/tcp
# nvd-service-1                           Up (healthy)        0.0.0.0:8002->8002/tcp
# ml-prediction-service-1                 Up (healthy)        0.0.0.0:8001->8001/tcp
# nmap-scanner-service-1                  Up (healthy)        0.0.0.0:8004->8004/tcp
# frontend-1                              Up                  0.0.0.0:5173->80/tcp
```

**Health Checks**:
```bash
# Backend
curl http://localhost:8000/api/v1/health
# Respuesta: {"status": "healthy", "services": {...}}

# NVD Service
curl http://localhost:8002/api/v1/health
# Respuesta: {"status": "healthy", "services": {"nvd_api": "healthy", "queue": "healthy"}}
```

---

### 2. Evidenciar RabbitMQ (CloudAMQP)

**Verificar Conexión**:
```bash
# Logs del NVD Service
docker-compose logs nvd-service | grep -i "rabbitmq"

# Salida esperada:
# INFO - Parsed RabbitMQ connection: host=chimpanzee.rmq.cloudamqp.com:5671
# INFO - QueueService: Conectado a RabbitMQ en chimpanzee.rmq.cloudamqp.com
```

**Dashboard de CloudAMQP**:
1. Acceder a: https://customer.cloudamqp.com/
2. Login con credenciales
3. Ver métricas:
   - **Messages Ready**: Mensajes en cola esperando procesamiento
   - **Messages Unacknowledged**: Mensajes siendo procesados
   - **Message Rate**: Mensajes/segundo (publish/deliver)
   - **Connections**: Conexiones activas (producers + consumers)

**Postman - Verificar Cola**:
```http
GET http://localhost:8002/api/v1/queue/status

Response:
{
  "queue_size": 5,
  "pending": 5,
  "processing": 2,
  "completed": 10,
  "queue_name": "nvd_analysis_queue",
  "status": "healthy"
}
```

---

### 3. Evidenciar Supabase (PostgreSQL)

**Verificar Conexión**:
```bash
# Logs del NVD Service
docker-compose logs nvd-service | grep -i "database\|supabase"

# Salida esperada:
# INFO - Connected to Supabase: postgresql://postgres.cjkgiqsfqykxrpnayslk@...
```

**Dashboard de Supabase**:
1. Acceder a: https://supabase.com/dashboard
2. Seleccionar proyecto: `cjkgiqsfqykxrpnayslk`
3. Table Editor:
   - Ver tabla `nvd_jobs`: Trabajos con estados
   - Ver tabla `nvd_vulnerabilities`: Vulnerabilidades encontradas

**Postman - Verificar Datos**:
```http
GET http://localhost:8002/api/v1/database/jobs

Response:
{
  "success": true,
  "total_jobs": 3,
  "jobs": [
    {
      "id": 7,
      "job_id": "1765978769481-1",
      "keyword": "python",
      "status": "completed",
      "total_results": 1154,
      "created_at": "2025-12-17T13:32:49.481Z",
      "processed_at": "2025-12-17T13:33:20.972Z",
      "processed_via": "queue_consumer"
    }
  ]
}
```

**SQL Query Directo**:
```sql
-- En Supabase SQL Editor
SELECT 
    job_id, 
    keyword, 
    status, 
    total_results,
    created_at,
    processed_at
FROM nvd_jobs
ORDER BY created_at DESC
LIMIT 10;
```

---

### 4. Evidenciar Time Service

**Test de Sincronización**:
```bash
# Crear 3 jobs simultáneamente desde diferentes clientes
curl -X POST "http://localhost:8000/api/v1/queue/job?keyword=apache" &
curl -X POST "http://localhost:8000/api/v1/queue/job?keyword=mysql" &
curl -X POST "http://localhost:8000/api/v1/queue/job?keyword=nginx" &

# Verificar timestamps en Supabase
curl http://localhost:8002/api/v1/database/jobs | jq '.jobs[] | {keyword, created_at}'

# Salida esperada (timestamps muy cercanos):
# {"keyword": "apache", "created_at": 1765978769.481}
# {"keyword": "mysql",  "created_at": 1765978769.482}
# {"keyword": "nginx",  "created_at": 1765978769.483}
```

**Logs de TimeService**:
```bash
docker-compose logs nvd-service | grep -i "timestamp\|worldtimeapi"

# Salida esperada:
# INFO - Using WorldTimeAPI timestamp: 1765978769.481
# INFO - Using WorldTimeAPI timestamp: 1765978800.972
```

**Fallback Test** (simular fallo de WorldTimeAPI):
```bash
# Bloquear acceso a WorldTimeAPI (editar /etc/hosts o firewall)
# Luego crear job
curl -X POST "http://localhost:8000/api/v1/queue/job?keyword=test"

# Logs mostrarán fallback:
# WARNING - WorldTimeAPI failed: Connection timeout, using local time
# INFO - Using local Docker time: 1765978850.123
```

---

### 5. Flujo End-to-End con Postman

**Colección de Postman**: `NVD_System_Tests.postman_collection.json`

#### Test 1: Crear Job
```http
POST http://localhost:8000/api/v1/queue/job?keyword=apache
Content-Type: application/json

Response (201 Created):
{
  "job_id": "1765978769481-1",
  "status": "queued",
  "keyword": "apache",
  "message": "Job added to queue"
}
```

**Evidencia**:
- ✅ Job creado en Supabase (estado: `pending`)
- ✅ Mensaje publicado en RabbitMQ
- ✅ Timestamp distribuido usado

#### Test 2: Iniciar Consumer
```http
POST http://localhost:8000/api/v1/queue/consumer/start

Response (200 OK):
{
  "message": "Consumer started",
  "status": "started"
}
```

**Evidencia**:
- ✅ Consumer thread iniciado
- ✅ Conexión a RabbitMQ establecida
- ✅ Logs muestran "Consumer started, waiting for messages..."

#### Test 3: Verificar Estado de Cola
```http
GET http://localhost:8000/api/v1/queue/status

Response (200 OK):
{
  "queue_size": 1,
  "pending": 1,
  "processing": 0,
  "completed": 0,
  "queue_name": "nvd_analysis_queue",
  "status": "healthy"
}
```

**Evidencia**:
- ✅ 1 mensaje en cola (el job de apache)
- ✅ Cola saludable

#### Test 4: Esperar Procesamiento (30-60s)
```bash
# Monitorear logs del consumer
docker-compose logs -f nvd-service

# Logs esperados:
# INFO - Processing job: 1765978769481-1 for keyword: apache
# INFO - Job 1765978769481-1 status updated to 'processing' in Supabase
# INFO - Fetching vulnerabilities for 'apache' from NVD API
# INFO - Found 250 vulnerabilities for 'apache'
# INFO - Successfully saved job to Supabase
# INFO - Job processed and completed: 1765978769481-1 (found 250 vulns)
```

#### Test 5: Obtener Resultados
```http
GET http://localhost:8000/api/v1/queue/results/all

Response (200 OK):
{
  "success": true,
  "jobs": [
    {
      "id": 7,
      "job_id": "1765978769481-1",
      "keyword": "apache",
      "status": "completed",
      "total_results": 250,
      "processed_at": 1765978800.972,
      "processed_via": "queue_consumer",
      "vulnerabilities": [
        {
          "cve": {
            "id": "CVE-2024-12345",
            "descriptions": [
              {
                "lang": "en",
                "value": "Apache HTTP Server vulnerability..."
              }
            ],
            "metrics": {
              "cvssMetricV31": [
                {
                  "cvssData": {
                    "baseScore": 7.5,
                    "baseSeverity": "HIGH"
                  }
                }
              ]
            }
          }
        }
        // ... 249 más
      ]
    }
  ]
}
```

**Evidencia**:
- ✅ Job completado (estado: `completed`)
- ✅ 250 vulnerabilidades encontradas
- ✅ Datos persistidos en Supabase
- ✅ Timestamps consistentes (created_at < processed_at)

---

### 6. Evidenciar Escalabilidad Horizontal

**Escalar NVD Service a 3 réplicas**:
```bash
docker-compose up --scale nvd-service=3 -d

# Verificar réplicas
docker-compose ps nvd-service
# Salida:
# nvd-service-1  Up
# nvd-service-2  Up
# nvd-service-3  Up
```

**Crear múltiples jobs**:
```bash
# Crear 10 jobs simultáneamente
for i in {1..10}; do
  curl -X POST "http://localhost:8000/api/v1/queue/job?keyword=test$i" &
done
```

**Verificar distribución de carga**:
```bash
# Logs de cada réplica
docker-compose logs nvd-service-1 | grep "Processing job"
docker-compose logs nvd-service-2 | grep "Processing job"
docker-compose logs nvd-service-3 | grep "Processing job"

# Salida esperada (jobs distribuidos):
# nvd-service-1: Processing job: ...-1, ...-4, ...-7, ...-10
# nvd-service-2: Processing job: ...-2, ...-5, ...-8
# nvd-service-3: Processing job: ...-3, ...-6, ...-9
```

**Evidencia**:
- ✅ RabbitMQ distribuye mensajes entre 3 consumers (round-robin)
- ✅ Procesamiento paralelo (3 jobs simultáneos)
- ✅ Throughput aumenta ~3x

---

### 7. Evidenciar Tolerancia a Fallos

**Test 1: Matar Consumer**:
```bash
# Crear job
curl -X POST "http://localhost:8000/api/v1/queue/job?keyword=test"

# Matar consumer mientras procesa
docker-compose kill nvd-service

# Reiniciar
docker-compose up -d nvd-service

# Verificar: Job sigue en cola (no se perdió)
curl http://localhost:8000/api/v1/queue/status
# queue_size: 1 (mensaje no fue ACK, volvió a la cola)
```

**Test 2: Simular Fallo de NVD API**:
```bash
# Bloquear acceso a NVD API (editar /etc/hosts)
echo "127.0.0.1 services.nvd.nist.gov" >> /etc/hosts

# Crear job
curl -X POST "http://localhost:8000/api/v1/queue/job?keyword=test"

# Logs mostrarán reintentos
docker-compose logs nvd-service | grep -i "retry\|error"

# Salida esperada:
# ERROR - Error fetching vulnerabilities: Connection refused
# INFO - Retrying (attempt 2/3)...
# ERROR - Error fetching vulnerabilities: Connection refused
# INFO - Retrying (attempt 3/3)...
# ERROR - Max retries exceeded, marking job as failed
```

**Evidencia**:
- ✅ Sistema intenta 3 veces antes de fallar
- ✅ Job marcado como `failed` en Supabase
- ✅ Mensaje no se pierde (NACK sin requeue)

---

## Justificación Técnica de Componentes

### ¿Por qué RabbitMQ y no Kafka?

**RabbitMQ**:
- ✅ **Simplicidad**: Más fácil de configurar y operar
- ✅ **Latencia Baja**: ~1ms (vs Kafka ~10ms)
- ✅ **Message Routing**: Exchange types (direct, topic, fanout, headers)
- ✅ **Garantías**: Delivery acknowledgments (ACK/NACK)
- ✅ **Managed Service**: CloudAMQP (alta disponibilidad)

**Kafka**:
- ❌ **Complejidad**: Requiere Zookeeper/KRaft, más difícil de operar
- ✅ **Throughput Alto**: Millones de mensajes/segundo (overkill para este caso)
- ✅ **Persistencia**: Retención de mensajes por días/semanas
- ❌ **Latencia**: Mayor que RabbitMQ

**Decisión**: RabbitMQ es suficiente para este caso de uso (< 1000 jobs/día)

---

### ¿Por qué Supabase y no MongoDB?

**Supabase (PostgreSQL)**:
- ✅ **ACID**: Transacciones, integridad referencial
- ✅ **SQL**: Queries complejas (JOINs, agregaciones)
- ✅ **JSONB**: Almacenamiento eficiente de datos semi-estructurados
- ✅ **Índices**: Búsqueda rápida (B-tree, GIN para JSONB)
- ✅ **Managed Service**: Backups automáticos, replicación

**MongoDB**:
- ✅ **Flexibilidad**: Schema-less
- ❌ **Consistencia**: Eventual consistency por defecto
- ❌ **Transacciones**: Limitadas (solo desde v4.0)

**Decisión**: PostgreSQL es mejor para datos estructurados con relaciones (jobs ↔ vulnerabilities)

---

### ¿Por qué FastAPI y no Flask/Django?

**FastAPI**:
- ✅ **Async/Await**: Manejo eficiente de I/O no bloqueante
- ✅ **Performance**: 2-3x más rápido que Flask
- ✅ **Type Hints**: Validación automática con Pydantic
- ✅ **OpenAPI**: Documentación auto-generada (Swagger UI)
- ✅ **Modern**: Basado en estándares modernos (ASGI, HTTP/2)

**Flask**:
- ❌ **Síncrono**: Bloquea thread en I/O
- ❌ **Performance**: Menor que FastAPI
- ✅ **Simplicidad**: Más fácil para proyectos pequeños

**Django**:
- ❌ **Monolítico**: Framework full-stack (overkill para API)
- ❌ **Performance**: Menor que FastAPI
- ✅ **Batteries Included**: ORM, admin panel, etc.

**Decisión**: FastAPI es ideal para APIs de alto rendimiento con async I/O

---

### ¿Por qué Docker y no Kubernetes?

**Docker Compose**:
- ✅ **Simplicidad**: Configuración en un solo archivo YAML
- ✅ **Desarrollo Local**: Fácil de ejecutar en laptop
- ✅ **Suficiente**: Para < 10 servicios

**Kubernetes**:
- ❌ **Complejidad**: Requiere cluster, ingress, services, deployments
- ✅ **Escalabilidad**: Auto-scaling, rolling updates
- ✅ **Producción**: Ideal para > 10 servicios, alta disponibilidad

**Decisión**: Docker Compose es suficiente para desarrollo y despliegues pequeños. Para producción a gran escala, migrar a Kubernetes.

---

## Conclusión

Este sistema implementa una **arquitectura de microservicios distribuidos** robusta que cumple con los principios fundamentales de sistemas distribuidos:

✅ **Desacoplamiento**: Servicios independientes comunicados por mensajería  
✅ **Escalabilidad**: Réplicas de servicios + load balancing  
✅ **Tolerancia a Fallos**: Retry logic + circuit breaker + message durability  
✅ **Consistencia Eventual**: Aceptable para análisis de vulnerabilidades  
✅ **Sincronización de Tiempo**: TimeService con fallback  
✅ **Observabilidad**: Logs estructurados + health checks  

**Tecnologías Clave**:
- **Frontend**: React + Vite
- **API Gateway**: FastAPI (Python)
- **Microservices**: FastAPI + Pika (RabbitMQ)
- **Message Broker**: RabbitMQ (CloudAMQP)
- **Database**: PostgreSQL (Supabase)
- **Time Sync**: WorldTimeAPI + Docker Time
- **Containerization**: Docker + Docker Compose

**Evidencia de Sistema Distribuido**:
- ✅ Múltiples nodos independientes (frontend, backend, nvd-service, rabbitmq, supabase)
- ✅ Comunicación por red (HTTP, AMQP, PostgreSQL protocol)
- ✅ Procesamiento asíncrono (producer-consumer pattern)
- ✅ Escalabilidad horizontal (réplicas de servicios)
- ✅ Tolerancia a fallos (retry, circuit breaker, message durability)
- ✅ Sincronización de tiempo distribuido (TimeService)

---

**Autor**: Sistema de Gestión de Riesgos Cuantitativos  
**Fecha**: 2025-12-17  
**Versión**: 1.0
