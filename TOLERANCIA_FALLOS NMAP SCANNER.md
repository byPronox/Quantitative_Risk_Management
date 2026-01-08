# 🛡️ Arquitectura de Sistema Distribuido y Tolerancia a Fallos - QRM

Este documento detalla la arquitectura técnica del proyecto **Quantitative Risk Management (QRM)**, justificando su diseño como sistema distribuido, su capacidad de tolerancia a fallos y el modelo operativo implementado.

---

## 1. 🌐 ¿Por qué un Sistema Distribuido?

El sistema QRM no es una aplicación monolítica tradicional, sino un ecosistema de **microservicios independientes** que se comunican entre sí. Esta arquitectura fue elegida para garantizar:

*   **Desacoplamiento**: Cada servicio tiene una responsabilidad única y clara.
*   **Escalabilidad Independiente**: Podemos escalar el servicio de escaneo (que consume mucha CPU) sin afectar al backend o al frontend.
*   **Tecnología Agnóstica**: Cada microservicio puede usar la tecnología más adecuada para su tarea (Python para ML, Node.js para I/O, etc.).

### Componentes del Ecosistema:

1.  **Backend Service (Django)**: Gestión de usuarios, lógica de negocio central.
2.  **NVD Service (Python)**: Sincronización y consulta de vulnerabilidades (NIST).
3.  **ML Service (Python)**: Modelos de predicción de riesgo.
4.  **Nmap Scanner Service (Node.js)**: Ejecución de escaneos de red (intensivo).
5.  **Frontend (React)**: Interfaz de usuario.
6.  **Health Monitor (Node.js)**: *Nuevo componente* para vigilancia y alertas.

---

## 2. 🛡️ Tolerancia a Fallos y Resiliencia

La característica más crítica de este sistema es su capacidad para **seguir operando parcialmente** incluso cuando uno de sus componentes falla.

### Escenario de Fallo: Caída del Escáner
Si el `nmap-scanner-service` deja de funcionar (por error de memoria, bloqueo, etc.):

1.  **El Frontend sigue accesible**: Los usuarios pueden ver reportes históricos y navegar.
2.  **El Backend sigue respondiendo**: La autenticación y gestión de activos funciona.
3.  **NVD y ML siguen operativos**: Se pueden consultar vulnerabilidades y predicciones previas.

**El sistema NO colapsa.** Solo la funcionalidad específica de "iniciar nuevos escaneos" se ve afectada temporalmente, pero el negocio continúa.

---

## 3. ⏰ Modelo Operativo 8/5 y Monitoreo Activo

El sistema está diseñado para operar bajo un modelo **8/5 (8 horas diarias, 5 días a la semana)**, alineado con el horario laboral estándar de la organización.

### ¿Por qué es crítico el monitoreo en este modelo?
A diferencia de un sistema 24/7 donde suele haber rotación de personal, en un modelo 8/5 es vital maximizar la disponibilidad durante las horas productivas.

*   **Detección Inmediata**: Si el servicio de escaneo cae a las 10:00 AM, no podemos esperar a que un usuario lo reporte a las 3:00 PM.
*   **Health Monitor**: Hemos implementado un "vigilante" automatizado que chequea la salud de los servicios críticos cada **30 segundos**.
*   **Notificación Proactiva**: El sistema envía un email a los administradores (`justingomezcoello@gmail.com`) en el momento exacto del fallo.

---

## 4. 🏥 El Guardián: Health Monitor Service

Es un microservicio ligero diseñado con un único propósito: **Asegurar la disponibilidad**.

### Funcionamiento Técnico:
1.  **Heartbeat Check**: Realiza una petición HTTP `GET /api/v1/health` al servicio de escaneo cada 30 segundos.
2.  **Lógica de Reintentos**: Para evitar falsos positivos, requiere **3 fallos consecutivos** (ventana de 90 segundos) antes de declarar una emergencia.
3.  **Alertas SMTP**: Se conecta a un servidor de correo (actualmente Mailtrap para pruebas, configurable para Outlook/Gmail) para enviar alertas detalladas.
4.  **Auto-Recuperación**: Continúa monitoreando y notifica automáticamente cuando el servicio vuelve a estar "Saludable".

---

## 5. 🧪 Guía de Verificación (Evidence)

Para demostrar la robustez del sistema, se puede ejecutar el siguiente protocolo de pruebas:

### Paso 1: Verificar Estado Saludable
Con todos los servicios corriendo:
```bash
# El monitor debe reportar estado saludable en los logs
docker-compose logs -f health-monitor
```

### Paso 2: Simular Catástrofe (Caída de Servicio)
Detenemos intencionalmente el servicio crítico:
```bash
docker-compose stop nmap-scanner-service
```

### Paso 3: Comprobar Tolerancia a Fallos (Independencia)
Mientras el escáner está "muerto", verificamos que el resto de la empresa sigue funcionando:

*   **Backend**: `curl http://localhost:8000/api/v1/health` ✅ (Responde 200 OK)
*   **NVD**: `curl http://localhost:8002/api/v1/health` ✅ (Responde 200 OK)
*   **Frontend**: Navegar a `http://localhost:5173` ✅ (Carga correctamente)

### Paso 4: Verificar Alerta Automática
Esperar 90 segundos y verificar la bandeja de entrada del correo configurado.
*   **Resultado**: Recibo de email con asunto `🚨 ALERTA: nmap-scanner-service CAÍDO`.

### Paso 5: Recuperación
```bash
docker-compose start nmap-scanner-service
```
*   **Resultado**: El sistema detecta la recuperación y envía un email de confirmación `✅ RECUPERADO`.

---

## 6. 📊 Conclusión

La implementación de esta arquitectura distribuida con monitoreo activo garantiza que **Quantitative Risk Management** sea un sistema:
1.  **Robusto**: Resistente a fallos individuales.
2.  **Confiable**: Con detección de problemas en tiempo real.
3.  **Profesional**: Adecuado para entornos empresariales con SLAs definidos.
