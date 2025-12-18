# 🏗️ Arquitectura del Sistema Distribuido - Nmap Scanner

Este documento detalla la arquitectura técnica del sistema de escaneo de vulnerabilidades distribuido, explicando los componentes, el flujo de datos, las rutas de API y las pruebas para verificar su naturaleza distribuida.

## 📐 Diagrama de Arquitectura

```mermaid
graph TD
    User[Usuario] -->|HTTP/HTTPS| Frontend[Frontend (React + Vite)]
    Frontend -->|HTTP Requests| Kong[Kong Cloud Gateway]
    
    subgraph "API Layer"
        Kong -->|Rate Limiting & Auth| Backend[Backend (FastAPI)]
    end
    
    subgraph "Message Broker"
        Backend -->|Publish Job| RabbitMQ[RabbitMQ Cloud]
    end
    
    subgraph "Microservices Layer"
        RabbitMQ -->|Consume Job| Scanner[Nmap Scanner Service]
        Scanner -->|Execute Scan| Target[Target IP/Host]
    end
    
    subgraph "Data Persistence"
        Scanner -->|Store Results| Supabase[Supabase (PostgreSQL)]
        Backend -->|Read Results| Supabase
        Frontend -->|Real-time Subs| Supabase
    end
    
    subgraph "Infrastructure"
        Time[WorldTimeAPI] -->|Sync| Backend
        Time -->|Sync| Scanner
    end
```

## 🧩 Componentes del Sistema

### 1. Frontend (React + Vite)
- **Puerto**: 5173
- **Tecnología**: React, TailwindCSS, Vite.
- **Función**: Interfaz de usuario reactiva. No procesa datos pesados; delega todo al backend.
- **Interacción**: Se comunica con el Backend a través del API Gateway y se suscribe a Supabase para actualizaciones en tiempo real.

### 2. Kong Cloud Gateway
- **Función**: API Gateway centralizado.
- **Justificación**: En un sistema distribuido, es crucial tener un punto único de entrada para manejar preocupaciones transversales como autenticación, rate limiting y logging, sin sobrecargar a los microservicios individuales.

### 3. Backend (FastAPI - Python)
- **Puerto**: 8000
- **Tecnología**: Python, FastAPI.
- **Función**: Orquestador y Productor de Mensajes.
- **Rol en Sistema Distribuido**: Actúa como "Producer" en el patrón Producer-Consumer. Recibe la petición HTTP del usuario, valida los datos y coloca un mensaje en la cola de RabbitMQ. **No espera a que termine el escaneo** para responder al usuario, garantizando una respuesta rápida (Non-blocking I/O).

### 4. RabbitMQ Cloud (Message Broker)
- **Tecnología**: AMQP 0-9-1.
- **Función**: Cola de mensajes persistente.
- **Justificación**: Es el corazón del desacoplamiento. Permite que el Backend y el Scanner operen a velocidades diferentes. Si hay un pico de 1000 peticiones, RabbitMQ las almacena (buffer) y los Scanners las procesan a su ritmo, evitando la caída del sistema.

### 5. Nmap Scanner Service (Node.js)
- **Puerto**: 8004
- **Tecnología**: Node.js, node-libnmap.
- **Función**: Microservicio Consumidor (Worker).
- **Rol en Sistema Distribuido**: Escucha pasivamente la cola. Cuando llega un mensaje, ejecuta el proceso pesado (`nmap`). Es "stateless" (sin estado), lo que significa que podemos levantar 10 instancias de este servicio para procesar 10 escaneos en paralelo sin conflictos.

### 6. Supabase (PostgreSQL)
- **Función**: Base de datos distribuida y capa de persistencia.
- **Características**: Almacena historial de escaneos, detalles de vulnerabilidades y estados de la cola.

---

## 🛣️ Rutas de API (Endpoints)

El sistema expone los siguientes endpoints principales a través del Gateway:

### Gestión de Cola (Queue Management)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `POST` | `/api/v1/nmap/queue/job` | **Productor**: Recibe una IP (`target_ip`) y la agrega a la cola de RabbitMQ. Retorna un `job_id` inmediatamente. |
| `GET` | `/api/v1/nmap/queue/status` | **Monitor**: Consulta a RabbitMQ cuántos mensajes hay en cola, procesando y completados. |
| `GET` | `/api/v1/nmap/queue/results/all` | **Consulta**: Obtiene el historial de todos los trabajos procesados. |

### Control del Consumidor (Consumer Control)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `POST` | `/api/v1/nmap/queue/consumer/start` | **Worker Control**: Ordena al microservicio de escaneo que comience a escuchar la cola. |
| `POST` | `/api/v1/nmap/queue/consumer/stop` | **Worker Control**: Ordena al microservicio que deje de escuchar (pausa el procesamiento). |

---

## 🧪 Pruebas de Verificación de Sistema Distribuido

Para comprobar que el sistema es realmente distribuido y cumple con las características de desacoplamiento y tolerancia a fallos, realice las siguientes pruebas:

### Prueba 1: Desacoplamiento y Asincronía (Queue Buffering)
**Objetivo**: Demostrar que el backend acepta trabajos incluso si el consumidor (scanner) está apagado.

1.  **Detener el Consumidor**:
    *   En el Frontend, haga clic en "⏹️ Detener Consumidor".
    *   O envíe POST a `/api/v1/nmap/queue/consumer/stop`.
2.  **Enviar Trabajos**:
    *   Envíe 3 IPs diferentes para escanear (ej: `scanme.nmap.org`, `google.com`, `1.1.1.1`).
    *   **Resultado Esperado**: El sistema responde "✅ IP agregada a la cola" inmediatamente para cada una.
    *   **Verificación**: En el panel de "Estado de RabbitMQ", verá "En Cola: 3" y "Pendientes: 3". El backend NO falló, aunque nadie esté procesando.
3.  **Iniciar Consumidor**:
    *   Haga clic en "▶️ Iniciar Consumidor".
    *   **Resultado Esperado**: El contador de "En Cola" baja y "Procesando" sube. Los trabajos se ejecutan uno a uno (o en paralelo si hay múltiples workers).

### Prueba 2: Tolerancia a Fallos (Fault Tolerance)
**Objetivo**: Simular la caída del servicio de escaneo.

1.  Asegúrese de que hay trabajos en la cola.
2.  **Matar el contenedor del scanner** (simulación de crash):
    *   `docker stop nmap-scanner-service`
3.  **Enviar otro trabajo**:
    *   El backend sigue aceptando el trabajo y lo guarda en RabbitMQ.
4.  **Recuperación**:
    *   `docker start nmap-scanner-service`
    *   **Resultado Esperado**: El servicio arranca, se reconecta a RabbitMQ y comienza a procesar los trabajos pendientes automáticamente. ¡No se perdió ningún dato!

---

## 🚀 Ejemplos para Postman

Puede importar estos ejemplos en Postman para interactuar directamente con la API.

### 1. Enviar Trabajo a la Cola (Producer)
**URL**: `http://localhost:8000/api/v1/nmap/queue/job`
**Method**: `POST`
**Params**: `target_ip` = `scanme.nmap.org`

**cURL**:
```bash
curl -X POST "http://localhost:8000/api/v1/nmap/queue/job?target_ip=scanme.nmap.org" \
     -H "accept: application/json"
```

**Respuesta Exitosa**:
```json
{
  "success": true,
  "message": "Job added to queue",
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued"
}
```

### 2. Consultar Estado de la Cola
**URL**: `http://localhost:8000/api/v1/nmap/queue/status`
**Method**: `GET`

**cURL**:
```bash
curl -X GET "http://localhost:8000/api/v1/nmap/queue/status" \
     -H "accept: application/json"
```

**Respuesta**:
```json
{
  "queue_size": 2,
  "consumer_status": "running",
  "jobs": {
    "pending": 2,
    "processing": 1,
    "completed": 15,
    "failed": 0
  }
}
```

### 3. Detener Consumidor (Simular Pausa)
**URL**: `http://localhost:8000/api/v1/nmap/queue/consumer/stop`
**Method**: `POST`

**cURL**:
```bash
curl -X POST "http://localhost:8000/api/v1/nmap/queue/consumer/stop" \
     -H "accept: application/json"
```

---

## 🛡️ Justificación de Análisis de Riesgos

El sistema no solo escanea, sino que interpreta. Utiliza una lógica de negocio distribuida para calcular el riesgo:

1.  **Ingesta**: El Scanner recibe datos crudos XML de Nmap.
2.  **Procesamiento**:
    *   Normaliza los puertos y servicios.
    *   Consulta bases de datos de vulnerabilidades (simulado/NVD).
3.  **Cálculo**: Aplica la fórmula `(Severity*0.4 + Exposure*0.3 + Exploitability*0.2 + Impact*0.1)`.
4.  **Decisión**: Genera automáticamente una estrategia (Aceptar, Mitigar, Transferir, Evitar) con una justificación "PORQUE" basada en reglas predefinidas.

Esta lógica reside en el microservicio, manteniendo al backend ligero y enfocado solo en la orquestación HTTP.
