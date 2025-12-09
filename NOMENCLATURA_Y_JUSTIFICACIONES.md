# 📋 Nomenclatura y Justificaciones del Sistema de Gestión de Riesgos Cuantitativo

Este documento explica **exhaustivamente** el porqué de cada nombre, convención de nomenclatura, y decisión de diseño en el sistema. Cada elemento ha sido cuidadosamente nombrado siguiendo estándares de la industria y mejores prácticas de desarrollo.

---

## 🏗️ Arquitectura General del Sistema

### ¿Por qué "Quantitative Risk Management System"?

**Nombre:** `Quantitative_Risk_Management`

**Justificación:**
- **"Quantitative"**: Indica que el sistema utiliza métodos numéricos y estadísticos para evaluar riesgos, no evaluaciones cualitativas subjetivas
- **"Risk"**: El dominio principal del sistema - identificación, evaluación y mitigación de riesgos
- **"Management"**: Implica un proceso completo de gestión, no solo detección de riesgos
- **Guiones bajos**: Estándar en nombres de repositorios para evitar problemas de compatibilidad cross-platform

---

## 🐳 Documentación Detallada de Contenedores Docker

A continuación, se detalla cada contenedor (servicio) que compone el sistema, explicando su nombre, función técnica y función general.

### 1. `gateway` (API Gateway)

**1. ¿Por qué se llama así?**
- **Nombre:** `gateway`
- **Razón:** Actúa como la "puerta de entrada" única para todas las peticiones externas. Es un patrón de diseño estándar en microservicios.
- **Por qué no `api-gateway`:** Por brevedad y facilidad de uso en comandos Docker (`docker exec gateway`).

**2. ¿Qué hace? (Explicación Técnica)**
- **Router Central:** Recibe todas las peticiones HTTP del frontend (puerto 8080) y las redirige al microservicio correspondiente (`backend`, `nvd-service`, etc.) usando `httpx`.
- **Balanceo de Carga (Potencial):** Puede distribuir tráfico si hubiera múltiples instancias de un servicio.
- **Seguridad Unificada:** Maneja CORS, autenticación preliminar y rate limiting en un solo punto.
- **Tecnología:** FastAPI (Python).

**3. ¿Qué hace? (Explicación General)**
- Es como el **recepcionista** de un edificio de oficinas.
- Cuando usted (el usuario) pide algo, no va directamente a la oficina del especialista. Se lo pide al recepcionista, y él sabe exactamente a qué oficina enviarlo.
- Esto mantiene el orden y la seguridad, ya que nadie entra directo a las oficinas internas sin pasar por recepción.

---

### 2. `backend` (Core Service)

**1. ¿Por qué se llama así?**
- **Nombre:** `backend`
- **Razón:** Es el servicio "central" o "trasero" que maneja la lógica de negocio principal del sistema.
- **Por qué no `core-service`:** Por convención universal en desarrollo web full-stack.

**2. ¿Qué hace? (Explicación Técnica)**
- **Orquestador de Lógica:** Maneja la lógica de negocio que no pertenece a un microservicio específico.
- **Gestión de Base de Datos:** Es el principal responsable de escribir y leer de la base de datos PostgreSQL (`db`) usando SQLAlchemy.
- **Motor de Decisión:** Ejecuta algoritmos de Programación Dinámica para optimizar estrategias de mitigación.
- **Tecnología:** FastAPI (Python), SQLAlchemy.

**3. ¿Qué hace? (Explicación General)**
- Es el **cerebro** del sistema.
- Aquí es donde se toman las decisiones importantes, se guardan los archivos en el archivador (base de datos) y se coordinan las tareas generales.
- Si el Gateway es el recepcionista, el Backend es el gerente general.

---

### 3. `frontend` (User Interface)

**1. ¿Por qué se llama así?**
- **Nombre:** `frontend`
- **Razón:** Representa la parte "frontal" que el usuario ve y toca.
- **Por qué no `client`:** `frontend` es el término estándar de la industria para la capa de presentación web.

**2. ¿Qué hace? (Explicación Técnica)**
- **Renderizado de UI:** Sirve la aplicación React (SPA) al navegador del usuario.
- **Consumo de API:** Realiza peticiones HTTP asíncronas (Axios) al `gateway` para obtener datos.
- **Visualización:** Genera gráficos interactivos (Chart.js) y tablas dinámicas.
- **Tecnología:** React, Vite, Nginx (para servir los estáticos).

**3. ¿Qué hace? (Explicación General)**
- Es la **cara** del sistema.
- Es la pantalla bonita con botones y gráficos que usted usa.
- Se encarga de traducir sus clics en órdenes que el sistema entiende y de mostrarle las respuestas de forma visual y comprensible.

---

### 4. `db` (Database)

**1. ¿Por qué se llama así?**
- **Nombre:** `db`
- **Razón:** Abreviatura universal de "Database".
- **Por qué no `postgres`:** Para abstraer la tecnología específica. Si mañana cambiamos a MySQL, el nombre del servicio `db` puede seguir siendo el mismo en la configuración de los otros contenedores.

**2. ¿Qué hace? (Explicación Técnica)**
- **Persistencia Relacional:** Almacena datos estructurados de forma permanente (Usuarios, Historial de Escaneos, Activos).
- **Integridad de Datos:** Asegura que la información no se corrompa y mantenga sus relaciones (Foreign Keys).
- **Tecnología:** PostgreSQL 15.

**3. ¿Qué hace? (Explicación General)**
- Es el **archivador** de la empresa.
- Aquí se guarda todo lo que necesita recordarse para siempre: informes pasados, listas de usuarios, configuraciones.
- Es muy ordenado y seguro; nada se pierde aquí.

---

### 5. `rabbitmq` (Message Queue)

**1. ¿Por qué se llama así?**
- **Nombre:** `rabbitmq`
- **Razón:** Es el nombre específico de la tecnología.
- **Por qué no `queue`:** RabbitMQ tiene configuraciones muy específicas, y es útil para los ingenieros saber exactamente qué software de colas se está usando.

**2. ¿Qué hace? (Explicación Técnica)**
- **Broker de Mensajería:** Permite la comunicación asíncrona entre servicios.
- **Desacoplamiento:** El `nvd-service` puede enviar una tarea de "analizar vulnerabilidad" a la cola, y el `report-service` puede tomarla cuando esté libre, sin bloquear al primero.
- **Tecnología:** RabbitMQ 3 Management.

**3. ¿Qué hace? (Explicación General)**
- Es la **bandeja de entrada de correo** o una **línea de ensamblaje**.
- Si hay mucho trabajo, no se le tira todo al trabajador de golpe. Se ponen las tareas en una bandeja (cola).
- Los trabajadores van tomando tareas de la bandeja una por una a su propio ritmo. Esto evita que el sistema se colapse por exceso de trabajo.

---

### 6. `nmap-scanner-service`

**1. ¿Por qué se llama así?**
- **Nombre:** `nmap-scanner-service`
- **Razón:** Identifica claramente la herramienta subyacente (`nmap`) y su función (`scanner`).
- **Por qué no `network-scanner`:** Para ser transparentes sobre la dependencia técnica (Nmap) que requiere privilegios especiales de red.

**2. ¿Qué hace? (Explicación Técnica)**
- **Escaneo de Puertos:** Ejecuta comandos `nmap` contra IPs objetivo para detectar puertos abiertos (22, 80, 443, etc.).
- **Detección de Servicios:** Identifica qué software y versión corre en cada puerto.
- **Ejecución de Scripts NSE:** Corre scripts de Nmap para detectar vulnerabilidades conocidas (CVEs).
- **Tecnología:** Python, Nmap, Docker (con capacidades `NET_ADMIN`).

**3. ¿Qué hace? (Explicación General)**
- Es el **inspector de seguridad** o **detective**.
- Visita la "casa" (servidor) que le indicamos y revisa todas las puertas y ventanas (puertos).
- Reporta cuáles están abiertas, qué tipo de cerradura tienen y si alguna cerradura parece rota o vieja.

---

### 7. `nvd-service`

**1. ¿Por qué se llama así?**
- **Nombre:** `nvd-service`
- **Razón:** Se conecta específicamente a la **National Vulnerability Database (NVD)**.
- **Por qué no `vuln-service`:** Porque su fuente de verdad es específicamente la NVD del NIST.

**2. ¿Qué hace? (Explicación Técnica)**
- **Proxy de API:** Consulta la API pública del NIST para obtener detalles de CVEs (Common Vulnerabilities and Exposures).
- **Enriquecimiento de Datos:** Agrega puntuaciones de riesgo (CVSS) y descripciones a las vulnerabilidades detectadas.
- **Caché (MongoDB):** Guarda copias locales de las vulnerabilidades para no consultar repetidamente a la API externa (que tiene límites de velocidad).
- **Tecnología:** FastAPI, MongoDB (interno).

**3. ¿Qué hace? (Explicación General)**
- Es el **bibliotecario experto**.
- Cuando el detective (Nmap) encuentra algo sospechoso, le pregunta al bibliotecario.
- El bibliotecario consulta su enciclopedia gigante (NVD) y le dice: "Sí, eso es un fallo conocido de 2023, es muy peligroso y se arregla así".

---

### 8. `ml-prediction-service`

**1. ¿Por qué se llama así?**
- **Nombre:** `ml-prediction-service`
- **Razón:** `ml` (Machine Learning) y `prediction` describen exactamente su función.
- **Por qué no `ai-service`:** "AI" es muy genérico. "ML Prediction" es técnicamente preciso sobre lo que hace (modelos predictivos).

**2. ¿Qué hace? (Explicación Técnica)**
- **Inferencia de Modelos:** Carga modelos entrenados (Random Forest, Isolation Forest) para predecir anomalías o riesgos.
- **Procesamiento de Datos:** Transforma datos crudos de tráfico o logs en vectores de características para los modelos.
- **Tecnología:** Python, Scikit-learn, Pandas.

**3. ¿Qué hace? (Explicación General)**
- Es el **analista de riesgos** o **futurólogo**.
- Mira los patrones del pasado y del presente para predecir si algo malo podría pasar en el futuro.
- No busca fallos obvios (como el detective), sino comportamientos extraños que podrían indicar un problema sutil.

---

### 9. `report-service`

**1. ¿Por qué se llama así?**
- **Nombre:** `report-service`
- **Razón:** Su única responsabilidad es generar documentos (reportes).
- **Por qué no `pdf-generator`:** Porque podría generar CSV, HTML, etc. "Report" es el dominio, no el formato.

**2. ¿Qué hace? (Explicación Técnica)**
- **Generación de Documentos:** Recopila datos de `db` y `nvd-service` para compilar informes PDF o CSV.
- **Formato y Diseño:** Aplica plantillas y estilos a los datos crudos para hacerlos legibles.
- **Tecnología:** Python, ReportLab, Jinja2.

**3. ¿Qué hace? (Explicación General)**
- Es el **secretario** o **editor**.
- Toma todas las notas desordenadas del detective, el bibliotecario y el analista, y las pone en un documento bonito, limpio y organizado que el jefe (usted) pueda leer y firmar.

---

## 📁 Estructura de Directorios

### ¿Por qué `microservices/` y no `services/`?

**Directorio:** `microservices/`

**Justificación:**
- **Precisión arquitectónica**: Clarifica que seguimos el patrón de microservicios
- **Diferenciación**: Evita confusión con `backend/src/services/` (servicios de dominio)
- **Escalabilidad**: Indica que cada subdirectorio es un servicio independiente deployable
- **Documentación implícita**: Comunica la arquitectura del sistema a nuevos desarrolladores

### ¿Por qué `app/` dentro de cada servicio?

**Estructura:** `backend/app/`, `microservices/*/app/`

**Justificación:**
- **Estándar FastAPI**: Convención oficial documentada por FastAPI
- **Separación de concerns**: Distingue código de aplicación de configuración (Dockerfile, requirements.txt)
- **Compatibilidad Docker**: Facilita COPY y WORKDIR en Dockerfiles
- **Portabilidad**: Permite mover servicios fácilmente entre proyectos

### ¿Por qué `src/` en algunos lugares y `app/` en otros?

**Patrón diferenciado:**
- **`app/`**: Servicios Python/FastAPI (backend, microservicios)
- **`src/`**: Frontend React y servicios Node.js

**Justificación:**
- **Convenciones específicas por tecnología**: React usa `src/`, FastAPI usa `app/`
- **Consistencia con ecosistemas**: Cada tecnología tiene sus estándares establecidos
- **Herramientas de build**: Vite, Webpack esperan `src/` en frontend
- **Community standards**: Facilita onboarding de desarrolladores especializados

---



## 🔗 Endpoints y Rutas API

### ¿Por qué `/predict/cicids/` y `/predict/lanl/`?

**Estructura:** `/predict/{model_type}/`

**Justificación:**
- **Versionado por modelo**: Permite diferentes versiones de modelos simultáneamente
- **A/B Testing**: Facilita comparación de rendimiento entre modelos
- **Backwards compatibility**: Mantiene endpoints antiguos funcionando
- **Clear intent**: Desarrolladores saben exactamente qué modelo están llamando
- **Monitoring**: Métricas separadas por tipo de modelo para análisis de performance

### ¿Por qué `/nvd/add_to_queue` en lugar de `/nvd/queue`?

**Justificación:**
- **Verbosidad intencional**: Clarifica la acción específica que se está realizando
- **RESTful precision**: Evita ambigüedad entre GET y POST en `/queue`
- **Self-documenting**: El endpoint se explica a sí mismo
- **Error prevention**: Reduce errores de desarrolladores que no leen documentación
- **Audit trail clarity**: Logs más claros sobre qué operaciones se realizan

### ¿Por qué `/health` y no `/status` o `/ping`?

**Justificación:**
- **Kubernetes standard**: Convención oficial para health checks
- **Industry adoption**: Usado por Spring Boot, Express.js, FastAPI
- **Comprehensive meaning**: Implica verificación completa de salud del servicio
- **Monitoring tools compatibility**: Prometheus, Grafana esperan `/health`
- **Cloud native patterns**: Estándar en AWS ELB, GCP Load Balancer

---

## 📊 Modelos de Datos y Schemas

### ¿Por qué `risk_models.py` y no `models.py`?

**Justificación:**
- **Domain specificity**: Clarifica que son modelos del dominio de riesgos
- **Namespace collision prevention**: Evita conflicto con `database_models.py`
- **Scalability**: Permite agregar `user_models.py`, `report_models.py`
- **Code organization**: Facilita navegación en IDEs con múltiples archivos model
- **Team development**: Diferentes desarrolladores pueden trabajar en diferentes dominios

### ¿Por qué `database_models.py` y no `orm_models.py`?

**Justificación:**
- **Clarity of purpose**: Clarifica que son modelos para persistencia
- **Technology agnostic**: Funciona con SQLAlchemy, Django ORM, Peewee
- **Separation of concerns**: Distingue modelos de negocio de modelos de datos
- **Maintenance**: Facilita encontrar código relacionado con esquemas de DB

---

## 🎯 Componentes Frontend

### ¿Por qué `AssetList.jsx` y no `Assets.jsx`?

**Justificación:**
- **Component purpose clarity**: Especifica que es una lista, no un asset individual
- **React conventions**: Sigue patrones de componentes como UserList, ProductList
- **Reusability**: Permite agregar `AssetCard.jsx`, `AssetForm.jsx` sin confusión
- **Props predictability**: Desarrolladores esperan props como `assets` array

### ¿Por qué `CombinedAnalysisForm.jsx`?

**Justificación:**
- **Functionality description**: Clarifica que combina múltiples tipos de análisis
- **Component complexity indication**: Sugiere que es un componente complejo
- **Feature evolution**: Permite refactoring a componentes más específicos
- **User story alignment**: Alinea con requerimiento "Como usuario quiero análisis combinado"

### ¿Por qué `AsyncSoftwareAnalysis.jsx`?

**Justificación:**
- **Async pattern indication**: Clarifica que maneja operaciones asíncronas
- **Performance implications**: Sugiere que es un componente de carga pesada
- **State management complexity**: Indica que maneja estados complejos (loading, error, success)
- **User experience**: Clarifica que necesita indicadores de progreso

### ¿Por qué `NvdRiskPie.jsx` y no `PieChart.jsx`?

**Justificación:**
- **Domain specificity**: Clarifica que es específico para datos NVD
- **Reusability boundaries**: Permite `GeneralPieChart.jsx` para otros usos
- **Data structure coupling**: Indica que espera estructura específica de datos NVD
- **Maintenance scope**: Facilita encontrar componentes relacionados con NVD

---

## 🗂️ Servicios y Controladores

### ¿Por qué separar `services/` y `controllers/`?

**Justificación arquitectónica:**
- **Clean Architecture**: Separa lógica de negocio (services) de manejo de requests (controllers)
- **Testability**: Services se pueden testear sin HTTP layer
- **Reusability**: Services se pueden usar desde diferentes controllers
- **Single Responsibility**: Controllers manejan HTTP, Services manejan business logic
- **Dependency Injection**: Facilita inyección de dependencias y mocking

### ¿Por qué `enhanced_risk_service.py`?

**Justificación:**
- **Version evolution**: Indica que es una versión mejorada de `risk_service.py`
- **Feature richness**: Sugiere funcionalidades adicionales
- **Migration path**: Permite migración gradual del servicio anterior
- **Backwards compatibility**: Mantiene el servicio anterior funcionando durante transición

### ¿Por qué `ml_prediction_controller.py` tan específico?

**Justificación:**
- **Single Responsibility**: Un controller por dominio específico
- **Error handling specialization**: Cada controller maneja errores específicos de su dominio
- **Middleware application**: Diferentes middlewares para diferentes tipos de requests
- **Rate limiting**: Diferentes límites de rate para diferentes operaciones
- **Monitoring granularity**: Métricas específicas por tipo de operación

---

## 🔧 Configuración y Variables de Entorno

### ¿Por qué `VITE_API_URL` y no `API_URL`?

**Justificación:**
- **Vite requirement**: Vite requiere prefijo `VITE_` para variables accesibles en browser
- **Security**: Solo variables con prefijo se exponen al cliente
- **Build time optimization**: Vite puede optimizar estas variables en build time
- **Framework convention**: Estándar documentado por Vite

### ¿Por qué `DATABASE_URL` en lugar de `DB_CONNECTION_STRING`?

**Justificación:**
- **Industry standard**: Usado por Heroku, Railway, Vercel
- **Library compatibility**: SQLAlchemy, Prisma, Django esperan `DATABASE_URL`
- **12-Factor App**: Sigue principios de configuración externa
- **Cloud deployment**: Compatible con la mayoría de providers cloud

### ¿Por qué `NVD_API_KEY` y no `NIST_API_KEY`?

**Justificación:**
- **Service specificity**: Clarifica que es específicamente para NVD API
- **Configuration clarity**: Evita confusión con otras APIs de NIST
- **Environment management**: Facilita gestión en múltiples environments
- **Security audit**: Facilita identificar qué servicios usan qué credenciales

---

## 📦 Archivos de Configuración

### ¿Por qué `docker-compose.yml` y no `docker-compose.yaml`?

**Justificación:**
- **Docker official preference**: Docker documentación oficial usa `.yml`
- **Brevity**: Extensión más corta, más rápida de escribir
- **Ecosystem consistency**: La mayoría de proyectos open source usan `.yml`
- **Tool compatibility**: Algunas herramientas legacy prefieren `.yml`

### ¿Por qué `requirements.txt` y no `pyproject.toml`?

**Justificación:**
- **Simplicity**: Más fácil de entender para developers junior
- **Docker optimization**: Mejor caching en Docker layers con pip
- **CI/CD compatibility**: Todas las herramientas CI soportan requirements.txt
- **Team familiarity**: Más developers conocen requirements.txt

### ¿Por qué `package.json` estándar en lugar de workspace?

**Justificación:**
- **Service independence**: Cada servicio maneja sus propias dependencias
- **Deployment separation**: Permite deployments independientes
- **Version management**: Diferentes servicios pueden usar diferentes versiones de librerías
- **Container optimization**: Cada container solo incluye dependencias necesarias

---

## 🏷️ Convenciones de Nombrado Específicas

### Variables y Funciones

#### ¿Por qué `snake_case` en Python?

**Justificación:**
- **PEP 8**: Estándar oficial de Python definido en PEP 8
- **Readability**: Más legible para funciones y variables largas
- **Library consistency**: Todas las librerías estándar de Python usan snake_case
- **Tooling support**: Linters y IDEs esperan snake_case en Python

#### ¿Por qué `camelCase` en JavaScript?

**Justificación:**
- **ECMAScript standard**: Convención oficial de JavaScript
- **Framework consistency**: React, Vue, Angular usan camelCase
- **Browser API alignment**: APIs nativas del browser usan camelCase
- **JSON compatibility**: JSON standards prefieren camelCase

### Clases y Componentes

#### ¿Por qué `PascalCase` para componentes React?

**Justificación:**
- **React requirement**: React requiere componentes en PascalCase
- **JSX distinction**: Distingue componentes personalizados de HTML elements
- **Component hierarchy**: Facilita identificar componentes en árbol de renderizado
- **Import clarity**: Hace obvio que se está importando un componente

#### ¿Por qué `PascalCase` para clases Python?

**Justificación:**
- **PEP 8 compliance**: Estándar oficial para clases en Python
- **OOP conventions**: Convención universal en programación orientada a objetos
- **Framework alignment**: FastAPI, SQLAlchemy usan PascalCase para clases
- **Type distinction**: Distingue clases de funciones y variables

### Archivos y Directorios

#### ¿Por qué `lowercase` para directorios?

**Justificación:**
- **Unix compatibility**: Sistemas Unix son case-sensitive
- **URL mapping**: Facilita mapping directo a URLs
- **Import simplicity**: Evita problemas de imports case-sensitive
- **Cross-platform**: Funciona consistentemente en Windows, Mac, Linux

#### ¿Por qué `kebab-case` para archivos Docker?

**Justificación:**
- **Docker convention**: Documentación oficial de Docker usa kebab-case
- **YAML compatibility**: YAML files comúnmente usan kebab-case
- **CLI consistency**: Docker CLI commands usan kebab-case
- **Registry compatibility**: Docker registries prefieren kebab-case

---

## 🏢 Patrones de Arquitectura

### ¿Por qué Repository Pattern?

**Implementación:** `repositories/risk_repository.py`

**Justificación:**
- **Data access abstraction**: Separa lógica de negocio de acceso a datos
- **Testability**: Facilita mocking de acceso a datos en tests
- **Database agnostic**: Permite cambiar de PostgreSQL a MongoDB sin cambiar services
- **DDD compliance**: Sigue principios de Domain Driven Design
- **Team scalability**: Diferentes desarrolladores pueden trabajar en diferentes layers

### ¿Por qué Factory Pattern?

**Implementación:** `PredictionFactory` en `ml/engine.py`

**Justificación:**
- **Model abstraction**: Permite agregar nuevos modelos sin cambiar código cliente
- **Configuration driven**: Permite selección de modelo via configuración
- **Resource optimization**: Carga modelos solo cuando son necesarios
- **Strategy pattern support**: Facilita intercambio de estrategias de predicción
- **Open/Closed principle**: Abierto para extensión, cerrado para modificación

### ¿Por qué Dependency Injection?

**Implementación:** FastAPI `Depends()` pattern

**Justificación:**
- **Loose coupling**: Componentes no dependen de implementaciones concretas
- **Testing**: Facilita inyección de mocks en tests
- **Configuration**: Permite diferentes configuraciones por environment
- **Monitoring**: Facilita inyección de logging y métricas
- **Performance**: Permite lazy loading y singleton patterns

---

## 🔍 Nomenclatura de Testing

### ¿Por qué `test_` prefix?

**Convención:** `test_integration.py`, `test_*.py`

**Justificación:**
- **pytest discovery**: pytest automáticamente descubre archivos con `test_` prefix
- **Industry standard**: Usado por pytest, unittest, nose
- **IDE integration**: IDEs reconocen automáticamente archivos de test
- **CI/CD automation**: Herramientas CI pueden automáticamente correr tests
- **File organization**: Clarifica propósito del archivo inmediatamente

### ¿Por qué `quick_test.py` y no `smoke_test.py`?

**Justificación:**
- **Accessibility**: "Quick" es más universalmente entendido que "smoke"
- **Purpose clarity**: Clarifica que es para verificaciones rápidas
- **Developer experience**: Más atractivo para developers correr "quick" tests
- **Time indication**: Sugiere que no toma mucho tiempo ejecutar

### ¿Por qué `health_check.py` separado?

**Justificación:**
- **Production monitoring**: Puede ser usado en producción para health checks
- **Dependency isolation**: No requiere dependencias de testing
- **Deployment verification**: Útil para verificar deployments exitosos
- **Monitoring integration**: Puede ser usado por herramientas de monitoring

---

## 📝 Documentación y Archivos Auxiliares

### ¿Por qué `README.md` en cada servicio?

**Justificación:**
- **Service independence**: Cada servicio puede ser entendido independientemente
- **Deployment documentation**: Instrucciones específicas por servicio
- **Developer onboarding**: Nuevos developers pueden entender servicios específicos
- **Maintenance**: Facilita mantenimiento por equipos especializados

### ¿Por qué `SECURITY.md`?

**Justificación:**
- **GitHub convention**: GitHub automáticamente muestra SECURITY.md
- **Vulnerability reporting**: Proceso claro para reportar vulnerabilidades
- **Compliance**: Requisito para muchos estándares de seguridad
- **Professional appearance**: Indica madurez del proyecto

### ¿Por qué `NOMENCLATURA_Y_JUSTIFICACIONES.md` (este archivo)?

**Justificación:**
- **Knowledge preservation**: Preserva decisiones de diseño para futuros developers
- **Onboarding acceleration**: Reduce tiempo de aprendizaje para nuevos team members
- **Consistency enforcement**: Ayuda a mantener consistencia en decisiones futuras
- **Architecture documentation**: Documenta el "why" además del "what"
- **Spanish language**: Alineado con la audiencia objetivo del proyecto

---

## 🚀 Nomenclatura de Deployment

### ¿Por qué `quick_start.sh` y `quick_start.ps1`?

**Justificación:**
- **Cross-platform support**: Soporta tanto Unix/Linux como Windows
- **Developer experience**: Un comando para empezar todo el proyecto
- **Consistency**: Mismo script funciona en development y staging
- **Automation**: Facilita CI/CD pipeline setup

### ¿Por qué `docker-compose` y no Kubernetes manifests?

**Justificación:**
- **Development simplicity**: Más fácil para desarrollo local
- **Resource requirements**: Menor overhead que Kubernetes cluster
- **Learning curve**: Más accessible para developers junior
- **Deployment flexibility**: Fácil migración a Kubernetes cuando sea necesario

### ¿Por qué puertos específicos (5173, 8080, 8000)?

**Puertos elegidos:**
- `5173`: Puerto default de Vite development server
- `8080`: Puerto común para API Gateways
- `8000`: Puerto default de FastAPI/uvicorn

**Justificación:**
- **Framework defaults**: Respeta configuraciones default de herramientas
- **Port conflict avoidance**: Puertos que raramente están en uso
- **Development convention**: Patrones reconocidos por developers
- **Documentation alignment**: Alinea con documentación oficial de frameworks

---

## 🧪 Nomenclatura de Ambientes y Configuración

### ¿Por qué `.env` files en lugar de config files?

**Justificación:**
- **12-Factor App**: Sigue principios de configuración por environment variables
- **Security**: Facilita exclusión de secrets del version control
- **Cloud compatibility**: Compatible con todos los cloud providers
- **Container support**: Docker y Kubernetes soportan nativamente .env files

### ¿Por qué `production`, `staging`, `development` environments?

**Justificación:**
- **Industry standard**: Convención universal en software development
- **Risk management**: Permite testing en staging antes de production
- **Development isolation**: Development no afecta otros environments
- **Compliance**: Requerido por muchos frameworks de compliance (SOX, GDPR)

---

## 📊 Nomenclatura de Monitoring y Observability

### ¿Por qué `/health` endpoints?

**Justificación:**
- **Kubernetes liveness probes**: Estándar para health checks
- **Load balancer integration**: ALB, NLB, HAProxy usan /health
- **Monitoring tools**: Prometheus, Datadog esperan /health endpoints
- **Simplicity**: Fácil de implementar y entender

### ¿Por qué logs estructurados en JSON?

**Justificación:**
- **Log aggregation**: ELK Stack, Splunk, CloudWatch prefieren JSON
- **Queryability**: JSON logs se pueden buscar y filtrar fácilmente
- **Machine readability**: Facilita alerting y monitoring automatizado
- **Standardization**: Formato estándar para microservicios

---

## 🔐 Nomenclatura de Seguridad

### ¿Por qué `API_KEY` en lugar de `TOKEN`?

**Justificación:**
- **Service specificity**: API keys son específicas por servicio
- **Rotation policy**: API keys tienen políticas de rotación diferentes
- **Access scope**: API keys típicamente tienen scope más limitado
- **Industry convention**: NVD, AWS, GCP usan término "API Key"

### ¿Por qué separar variables de entorno por servicio?

**Justificación:**
- **Principle of least privilege**: Cada servicio solo tiene acceso a sus credenciales
- **Security isolation**: Comprometimiento de un servicio no afecta otros
- **Audit trail**: Más fácil rastrear uso de credenciales específicas
- **Compliance**: Requerido por muchos frameworks de seguridad

---

## 📈 Nomenclatura de Performance y Escalabilidad

### ¿Por qué async/await patterns?

**Implementación:** `async def` en FastAPI, `useState` en React

**Justificación:**
- **Non-blocking I/O**: Mejora throughput de aplicación
- **Resource efficiency**: Menor uso de memory y CPU
- **User experience**: UI no se bloquea durante operaciones lentas
- **Scalability**: Permite manejar más requests concurrentes

### ¿Por qué message queues (RabbitMQ)?

**Justificación:**
- **Decoupling**: Servicios no necesitan estar disponibles simultáneamente
- **Reliability**: Messages se persisten hasta ser procesados
- **Scalability**: Múltiples consumers pueden procesar messages
- **Fault tolerance**: Sistema continúa funcionando si un servicio falla

---

## 🎨 Nomenclatura de UI/UX

### ¿Por qué `components/` y `pages/`?

**Justificación:**
- **React convention**: Estándar en ecosistema React
- **Reusability**: Components se reutilizan, pages son específicas
- **Routing clarity**: Pages se mapean directamente a rutas
- **Team organization**: Frontend developers saben dónde encontrar código

### ¿Por qué `.jsx` extension?

**Justificación:**
- **Syntax clarity**: Clarifica que archivo contiene JSX syntax
- **Tooling support**: IDEs y linters reconocen JSX automáticamente
- **Build optimization**: Bundlers pueden optimizar específicamente JSX files
- **Team communication**: Clarifica que archivo requiere React knowledge

---

## 🌍 Internacionalización y Localización

### ¿Por qué español en UI pero inglés en código?

**Justificación:**
- **User experience**: Usuarios finales ven contenido en español
- **Developer experience**: Código en inglés es estándar internacional
- **Maintainability**: Más fácil encontrar developers que lean código en inglés
- **Open source compatibility**: Facilita contribuciones de developers internacionales

### ¿Por qué mantener documentación técnica en inglés?

**Justificación:**
- **Industry standard**: Documentación técnica típicamente en inglés
- **Tool compatibility**: Muchas herramientas esperan inglés
- **Knowledge sharing**: Facilita compartir knowledge con comunidad global
- **Future hiring**: Expande pool de developers que pueden trabajar en proyecto

---

## 🔄 Versionado y Evolución

### ¿Por qué semantic versioning implícito?

**Justificación:**
- **API compatibility**: Cambios breaking se indican claramente
- **Deployment safety**: Facilita rollbacks seguros
- **Dependency management**: Otras aplicaciones pueden depender con confianza
- **Communication**: Clarifica impact of changes a stakeholders

### ¿Por qué feature flags implícitos en configuración?

**Justificación:**
- **Safe deployments**: Nuevas features se pueden activar gradualmente
- **A/B testing**: Facilita testing de diferentes approaches
- **Rollback capability**: Fácil desactivar features problemáticas
- **Continuous delivery**: Permite deployments frecuentes con menor riesgo

---

## 📋 Conclusiones sobre Nomenclatura

### Principios Generales Aplicados:

1. **Claridad sobre Brevedad**: Nombres descriptivos aunque sean más largos
2. **Consistencia**: Mismas convenciones en contextos similares
3. **Estándares de Industria**: Seguir convenciones establecidas
4. **Escalabilidad**: Nombres que permiten crecimiento del sistema
5. **Mantenibilidad**: Facilita understanding para futuros developers

### Beneficios del Sistema de Nomenclatura:

- **Onboarding Rápido**: Nuevos developers entienden sistema más rápido
- **Reduced Cognitive Load**: Menos decisiones que tomar sobre nombres
- **Better Collaboration**: Team habla "mismo idioma"
- **Easier Debugging**: Nombres descriptivos facilitan troubleshooting
- **Professional Appearance**: Sistema se ve maduro y bien pensado

---

**Autor:** Sistema de Gestión de Riesgos Cuantitativo  
**Fecha:** 2025  
**Versión:** 1.0  
**Propósito:** Documentar decisiones de nomenclatura para mantener consistencia y facilitar mantenimiento del sistema
