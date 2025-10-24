# Quantitative Risk Management System (QRMS)

Sistema integral de gestión de riesgos cuantitativos con análisis de vulnerabilidades, predicciones de ML y rubrica de mitigación de riesgos.

## 🚀 Nuevas Funcionalidades Implementadas

### 1. Sistema de Rubrica de Riesgos AVOID/MITIGATE/TRANSFER/ACCEPT

El sistema ahora implementa una rubrica completa de gestión de riesgos que proporciona recomendaciones específicas y técnicas para cada vulnerabilidad encontrada:

- **AVOID**: Eliminar o aislar completamente el activo
- **MITIGATE**: Aplicar parches, cerrar puertos, endurecer configuraciones  
- **TRANSFER**: Externalizar el riesgo mediante seguros o servicios especializados
- **ACCEPT**: Documentar y monitorear riesgos de bajo impacto

### 2. Análisis de Vulnerabilidades Mejorado

- **Escaneo simplificado**: Un solo tipo de escaneo nmap optimizado (`nmap -sV --script vuln`)
- **Análisis técnico detallado**: Cada vulnerabilidad incluye explicaciones técnicas específicas
- **Recomendaciones específicas**: Acciones concretas basadas en el tipo de vulnerabilidad y servicio
- **Evaluación de riesgo por servicio**: Análisis individual de cada servicio expuesto

### 3. Dashboard de Análisis de Riesgos

Nuevo componente frontend que muestra:
- Resumen general del riesgo con nivel crítico/alto/medio/bajo
- Análisis detallado de cada servicio encontrado
- Vulnerabilidades específicas con estrategias de mitigación
- Recomendaciones técnicas con acciones específicas
- Resumen de estrategias de mitigación aplicadas

## 🏗️ Arquitectura del Sistema

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   Microservices │
│   (React)       │◄──►│   (FastAPI)     │◄──►│                 │
│                 │    │                 │    │                 │
│ - Risk Dashboard│    │ - Risk Analysis │    │ - Nmap Scanner  │
│ - Scan Results  │    │ - NVD Proxy     │    │ - NVD Service   │
│ - Reports       │    │ - ML Proxy      │    │ - ML Service    │
└─────────────────┘    └─────────────────┘    │ - Report Service│
                                               └─────────────────┘
```

## 🛠️ Instalación y Configuración

### Prerrequisitos

- Docker y Docker Compose
- Python 3.8+
- Node.js 16+
- nmap (para el servicio de escaneo)

### Configuración Rápida

1. **Clonar el repositorio**
```bash
git clone <repository-url>
cd Quantitative_Risk_Management
```

2. **Configurar variables de entorno**
```bash
# El archivo .env ya está configurado con las URLs correctas
# Verificar que las URLs de Kong Gateway sean correctas
```

3. **Levantar todos los servicios**
```bash
docker-compose up -d
```

4. **Verificar que todo funcione**
```bash
python test_integration.py
```

### Servicios Incluidos

- **Backend (Puerto 8000)**: API Gateway principal
- **Frontend (Puerto 5173)**: Interfaz web React
- **Nmap Scanner (Puerto 8004)**: Servicio de escaneo de vulnerabilidades
- **NVD Service (Puerto 8002)**: Base de datos de vulnerabilidades
- **ML Service (Puerto 8001)**: Predicciones de riesgo con ML
- **Report Service (Puerto 8003)**: Generación de reportes
- **PostgreSQL (Puerto 5432)**: Base de datos principal
- **RabbitMQ (Puerto 5672)**: Cola de mensajes
- **Redis (Puerto 6379)**: Cache

## 📡 API Endpoints Principales

### Análisis de Riesgos con Rubrica

```http
POST /api/v1/risk/nmap-analysis
Content-Type: application/json

{
  "ip": "192.168.1.1",
  "include_vulnerability_analysis": true,
  "include_risk_rubric": true
}
```

**Respuesta:**
```json
{
  "target": "192.168.1.1",
  "overall_risk_level": "HIGH",
  "services_analysis": [
    {
      "port": "22",
      "service_name": "ssh",
      "risk_level": "HIGH",
      "mitigation_strategy": "Aplicar parches y controles de seguridad específicos",
      "recommended_actions": [
        "Aplicar parches de seguridad prioritarios",
        "Implementar autenticación multifactor",
        "Cerrar puertos innecesarios"
      ],
      "technical_details": "SSH es un protocolo crítico para administración remota..."
    }
  ],
  "vulnerabilities_analysis": [
    {
      "vulnerability_id": "ssh-banner",
      "severity": "MEDIUM",
      "mitigation_strategy": "Implementar controles de seguridad estándar",
      "technical_details": "Información de versión expuesta puede ayudar a atacantes..."
    }
  ],
  "risk_recommendations": [
    {
      "priority": "HIGH",
      "title": "Securizar servicio SSH en puerto 22",
      "actions": ["Aplicar parches", "Implementar MFA"],
      "technical_rationale": "Servicio presenta riesgos de seguridad significativos"
    }
  ]
}
```

### Estrategias de Mitigación

```http
GET /api/v1/risk/mitigation-strategies
```

### Análisis de Servicio Específico

```http
POST /api/v1/risk/analyze-service
Content-Type: application/json

{
  "ip": "192.168.1.1",
  "port": "22",
  "name": "ssh",
  "product": "OpenSSH",
  "version": "8.2"
}
```

## 🎯 Casos de Uso

### 1. Análisis de Red Interna
```bash
# Escanear servidor interno
curl -X POST http://localhost:8000/api/v1/risk/nmap-analysis \
  -H "Content-Type: application/json" \
  -d '{"ip": "192.168.1.100", "include_risk_rubric": true}'
```

### 2. Análisis de Servicio Web
```bash
# Analizar servidor web específico
curl -X POST http://localhost:8000/api/v1/risk/analyze-service \
  -H "Content-Type: application/json" \
  -d '{"ip": "example.com", "port": "80", "name": "http", "product": "Apache", "version": "2.4.41"}'
```

### 3. Evaluación de Base de Datos
```bash
# Analizar servidor de base de datos
curl -X POST http://localhost:8000/api/v1/risk/analyze-service \
  -H "Content-Type: application/json" \
  -d '{"ip": "db.example.com", "port": "3306", "name": "mysql", "product": "MySQL", "version": "8.0.25"}'
```

## 🔧 Configuración Avanzada

### Variables de Entorno Importantes

```bash
# Kong Gateway Configuration
KONG_PROXY_URL=https://kong-b27b67aff4usnsp19.kongcloud.dev
KONG_ADMIN_API=https://us.api.konghq.com/v2/control-planes/9d98c0ba-3ac1-44fd-b497-59743e18a80a

# NVD API Configuration
NVD_API_KEY=dc2624cc-b2a6-462b-b859-d7cf0ad1cf66
USE_KONG_NVD=true

# Service URLs
ML_SERVICE_URL=http://ml-prediction-service:8001
NVD_SERVICE_URL=http://nvd-service:8002
NMAP_SERVICE_URL=http://nmap-scanner-service:8004
```

### Personalización de Estrategias de Mitigación

Las estrategias de mitigación se pueden personalizar editando:
- `backend/src/services/enhanced_risk_service.py`
- Modificar los diccionarios `mitigation_strategies` y `service_risk_profiles`

## 📊 Interpretación de Resultados

### Niveles de Riesgo

- **CRITICAL**: Acción inmediata requerida (AVOID o MITIGATE)
- **HIGH**: Atención prioritaria (MITIGATE o TRANSFER)  
- **MEDIUM**: Implementar controles estándar (MITIGATE o ACCEPT)
- **LOW**: Monitorear y documentar (ACCEPT)

### Estrategias de Mitigación

- **AVOID**: Para vulnerabilidades críticas sin mitigación viable
- **MITIGATE**: Para vulnerabilidades con parches o controles disponibles
- **TRANSFER**: Para sistemas no críticos o recursos limitados
- **ACCEPT**: Para riesgos de bajo impacto o costo de mitigación alto

## 🚨 Solución de Problemas

### Servicios No Inician

```bash
# Verificar logs
docker-compose logs [service-name]

# Reiniciar servicios
docker-compose restart [service-name]

# Verificar estado
docker-compose ps
```

### Errores de Conexión

```bash
# Verificar conectividad entre servicios
docker-compose exec backend ping nmap-scanner-service
docker-compose exec backend ping nvd-service

# Verificar puertos
netstat -tulpn | grep :8000
```

### Problemas de nmap

```bash
# Verificar instalación de nmap
docker-compose exec nmap-scanner-service nmap --version

# Probar escaneo básico
docker-compose exec nmap-scanner-service nmap -sV 127.0.0.1
```

## 📈 Monitoreo y Logs

### Logs de Aplicación

```bash
# Ver todos los logs
docker-compose logs -f

# Logs específicos por servicio
docker-compose logs -f backend
docker-compose logs -f nmap-scanner-service
```

### Métricas de Rendimiento

- **Tiempo de escaneo**: ~2-5 minutos por objetivo
- **Límite de velocidad**: 10 escaneos por 15 minutos
- **Timeout**: 5 minutos máximo por escaneo

## 🔒 Consideraciones de Seguridad

1. **Permisos de nmap**: El servicio requiere privilegios especiales para escaneo de red
2. **Acceso a Kong**: Las credenciales de Kong deben mantenerse seguras
3. **API Keys**: Rotar regularmente las claves de NVD API
4. **Red interna**: Solo escanear redes autorizadas

## 🤝 Contribución

1. Fork el repositorio
2. Crear rama de feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request

## 📝 Licencia

Este proyecto está bajo la Licencia MIT. Ver `LICENSE` para más detalles.

## 📞 Soporte

Para soporte técnico o preguntas:
- Crear un issue en GitHub
- Revisar la documentación de API en `/docs`
- Verificar logs de servicios para errores específicos

---

**Nota**: Este sistema está diseñado para uso en redes autorizadas. Siempre obtener permisos antes de escanear sistemas externos.
