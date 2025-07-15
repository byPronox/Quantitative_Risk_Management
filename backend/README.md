# Backend - Risk Management API Gateway

Este es el backend refactorizado del sistema de gestión de riesgos cuantitativos, siguiendo las mejores prácticas de arquitectura de software.

## 🏗️ Arquitectura

### Estructura del Proyecto
```
backend/
├── src/                          # Código fuente principal
│   ├── config/                   # Configuración de la aplicación
│   │   ├── __init__.py
│   │   ├── settings.py          # Configuración centralizada
│   │   └── database.py          # Configuración de base de datos
│   ├── controllers/             # Controladores HTTP (API endpoints)
│   │   ├── __init__.py
│   │   ├── health_controller.py # Endpoints de salud
│   │   ├── risk_controller.py   # Endpoints de análisis de riesgo
│   │   └── nvd_controller.py    # Endpoints de NVD
│   ├── models/                  # Modelos de datos
│   │   ├── __init__.py
│   │   ├── risk_models.py       # Modelos Pydantic para API
│   │   └── database_models.py   # Modelos SQLAlchemy para DB
│   ├── services/                # Lógica de negocio
│   │   ├── __init__.py
│   │   ├── risk_service.py      # Servicio de análisis de riesgo
│   │   └── nvd_service.py       # Servicio de NVD API
│   ├── repositories/            # Acceso a datos
│   │   ├── __init__.py
│   │   └── risk_repository.py   # Repositorio de análisis de riesgo
│   ├── middleware/              # Middleware personalizado
│   │   ├── __init__.py
│   │   ├── error_handler.py     # Manejo de errores
│   │   └── logging_middleware.py # Logging de requests
│   ├── interfaces/              # Interfaces/contratos
│   │   ├── __init__.py
│   │   └── repository_interfaces.py
│   ├── main.py                  # Punto de entrada de la aplicación
│   └── __init__.py
├── .env                         # Variables de entorno
├── requirements.txt             # Dependencias Python
├── Dockerfile                   # Configuración Docker
├── check_migration.py           # Script de verificación
└── README.md                    # Este archivo
```

## 🚀 Características

### Mejoras Implementadas
- **Arquitectura Limpia**: Separación clara de responsabilidades
- **Configuración Centralizada**: Todas las configuraciones en un lugar
- **Manejo de Errores**: Middleware personalizado para errores
- **Logging**: Sistema de logging robusto
- **Modelos Tipados**: Uso de Pydantic para validación
- **Interfaces**: Contratos claros para servicios
- **Environment Security**: Variables sensibles movidas a .env

### Tecnologías
- **FastAPI**: Framework web moderno y rápido
- **SQLAlchemy**: ORM para PostgreSQL
- **MongoDB**: Base de datos NoSQL para datos detallados
- **Pydantic**: Validación y serialización de datos
- **HTTPX**: Cliente HTTP asíncrono
- **Uvicorn**: Servidor ASGI

## 🔧 Configuración

### Variables de Entorno

El archivo `.env` contiene todas las credenciales reales necesarias para la producción:

```env
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_VERSION=v1

# Kong Gateway Configuration
KONG_PROXY_URL=https://kong-b27b67aff4usnspl9.kongcloud.dev
KONG_ADMIN_API=https://us.api.konghq.com/v2/control-planes/9d98c0ba-3ac1-44fd-b497-59743e18a80a
KONG_CONTROL_PLANE_ID=9d98c0ba-3ac1-44fd-b497-59743e18a80a

# Database Configuration
DATABASE_URL=postgresql://postgres:postgres@db:5432/postgres
MONGODB_URL=mongodb+srv://ADMIN:ADMIN@cluster0.7ixig65.mongodb.net/
MONGODB_DATABASE=quantitative_risk_management

# NVD API Configuration
NVD_API_KEY=b0f20683-6364-4314-97cc-6f85ea75df67
USE_KONG_NVD=true

# RabbitMQ Configuration
RABBITMQ_HOST=rabbitmq
RABBITMQ_QUEUE=nvd_analysis_queue
RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/
```

**Nota**: Para desarrollo/distribución, usa `.env.example` que contiene plantillas sin credenciales reales.

### Instalación

1. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configurar variables de entorno**:
   ```bash
   cp .env.example .env
   # Editar .env con tus configuraciones
   ```

3. **Ejecutar la aplicación**:
   ```bash
   python src/main.py
   ```

### Docker

```bash
# Construir imagen
docker build -t risk-management-backend .

# Ejecutar contenedor
docker run -p 8000:8000 risk-management-backend
```

## 📖 API Endpoints

### Health Check
- `GET /api/v1/health` - Estado de la aplicación
- `GET /api/v1/health/services` - Estado de microservicios

### Risk Analysis
- `POST /api/v1/risk/analyze` - Analizar riesgo de activos
- `GET /api/v1/risk/reports` - Obtener reportes de riesgo
- `GET /api/v1/risk/matrix` - Matriz de riesgo para visualización

### NVD Integration
- `GET /api/v1/nvd/vulnerabilities` - Buscar vulnerabilidades
- `GET /api/v1/nvd/cpe` - Buscar CPE entries
- `POST /api/v1/nvd/analyze` - Analizar lista de software

## 🧪 Testing

### Verificar Configuración y Estructura
```bash
python verify_setup.py
```

Este script verifica:
- ✅ Archivo `.env` existe y tiene todas las variables requeridas
- ✅ No hay credenciales hardcodeadas en el código
- ✅ Estructura de directorios es correcta
- ✅ Archivos principales existen

### Verificar Migración de Estructura Anterior
```bash
python check_migration.py
```

### Probar API
```bash
# Health check
curl http://localhost:8000/api/v1/health

# API docs
open http://localhost:8000/api/v1/docs
```

## 🔒 Seguridad

### Mejoras de Seguridad Implementadas
- Variables sensibles movidas a `.env`
- Configuración centralizada sin hardcoding
- Manejo de errores que no expone información interna
- Logging de requests para auditoría
- Headers de seguridad en responses

### Variables Eliminadas del Código
- API keys hardcodeadas
- URLs de producción en el código
- Credenciales de base de datos
- Tokens de acceso

## 🔄 Migración desde Estructura Anterior

La estructura anterior `backend/app/` ha sido refactorizada a `backend/src/` con las siguientes mejoras:

### Antes
```
backend/app/
├── main.py
├── api/routes.py
├── config/config.py
├── database/
├── services/
└── middleware/
```

### Después
```
backend/src/
├── main.py                    # Mejorado
├── controllers/               # Antes: api/
├── config/                    # Mejorado
├── models/                    # Nuevo: separación de modelos
├── services/                  # Mejorado
├── repositories/              # Nuevo: separación de datos
├── middleware/                # Mejorado
└── interfaces/                # Nuevo: contratos
```

## 🚦 Próximos Pasos

1. **Probar la nueva estructura**:
   ```bash
   python check_migration.py
   python src/main.py
   ```

2. **Verificar funcionalidad**:
   - Probar endpoints en `/api/v1/docs`
   - Verificar conexiones a base de datos
   - Probar integración con microservicios

3. **Eliminar estructura anterior**:
   ```bash
   # Una vez verificado que todo funciona
   rm -rf backend/app/
   ```

4. **Actualizar docker-compose.yml** si es necesario

## 📝 Logs

Los logs se configuran automáticamente con diferentes niveles:
- `INFO`: Información general
- `ERROR`: Errores y excepciones
- `WARNING`: Advertencias

## 🤝 Contribución

Para contribuir:
1. Sigue la estructura de carpetas establecida
2. Añade tests para nueva funcionalidad
3. Actualiza este README si es necesario
4. Sigue las convenciones de nombrado de Python

---

**Nota**: Esta refactorización mejora significativamente la mantenibilidad, seguridad y escalabilidad del código.
