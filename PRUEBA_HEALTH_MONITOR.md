# 🧪 Guía de Prueba Completa - Health Monitor

## 📋 Objetivo
Demostrar que:
1. ✅ El health monitor detecta cuando `nmap-scanner` se cae
2. ✅ Envía notificación por email a `justingomezcoello@gmail.com`
3. ✅ Los demás servicios siguen funcionando independientemente

---

## 🚀 PASO 1: Reiniciar el Health Monitor

Primero, asegúrate de que el monitor tome la nueva configuración de email:

```bash
docker-compose restart health-monitor
```

**Verificar que está funcionando:**
```bash
docker-compose logs --tail=20 health-monitor
```

**Deberías ver:**
```
✅ [timestamp] nmap-scanner-service - Saludable (X chequeos)
```

---

## 🔥 PASO 2: Simular Caída del Servicio

### 2.1 Detener nmap-scanner

```bash
docker-compose stop nmap-scanner-service
```

**Esto simula que el servicio se cayó** (error, falta de recursos, etc.)

### 2.2 Observar la detección del fallo

```bash
docker-compose logs -f health-monitor
```

**Verás esta secuencia (~90 segundos total):**

```
🔍 Ejecutando chequeo de salud...
❌ [timestamp] nmap-scanner-service - Fallo 1/3
   Error: connect ECONNREFUSED

🔍 Ejecutando chequeo de salud...
❌ [timestamp] nmap-scanner-service - Fallo 2/3
   Error: connect ECONNREFUSED

🔍 Ejecutando chequeo de salud...
❌ [timestamp] nmap-scanner-service - Fallo 3/3
   Error: connect ECONNREFUSED

🚨 ALERTA: Enviando notificación de fallo...
✅ Email enviado: <message-id>
```

### 2.3 Revisar tu email

1. Abre tu correo: **justingomezcoello@gmail.com**
2. Busca el email (puede tardar 1-2 minutos)
3. **Revisa también SPAM** si no aparece

**Email esperado:**
- 🚨 Asunto: "ALERTA: nmap-scanner-service CAÍDO"
- Detalles del incidente, timestamp, comandos recomendados

---

## ✅ PASO 3: Verificar Independencia de Servicios

**Mientras `nmap-scanner` está detenido**, verifica que los otros servicios siguen funcionando:

### 3.1 Verificar Backend

```bash
curl http://localhost:8000/api/v1/health
```

**Resultado esperado:** ✅ Respuesta JSON con status "healthy"

### 3.2 Verificar NVD Service

```bash
curl http://localhost:8002/api/v1/health
```

**Resultado esperado:** ✅ Respuesta JSON con status "healthy"

### 3.3 Verificar ML Service

```bash
curl http://localhost:8001/health
```

**Resultado esperado:** ✅ Respuesta JSON

### 3.4 Verificar Frontend

Abre en el navegador: **http://localhost:5173**

**Resultado esperado:** ✅ La aplicación carga correctamente

**Solo la sección de Nmap Scanner** mostrará error, todo lo demás funciona.

---

## 🎉 PASO 4: Simular Recuperación

### 4.1 Reiniciar el servicio

```bash
docker-compose start nmap-scanner-service
```

### 4.2 Observar la recuperación

```bash
docker-compose logs -f health-monitor
```

**Verás:**
```
🔍 Ejecutando chequeo de salud...
✅ RECUPERACIÓN: Servicio restaurado
✅ Email enviado: <message-id>
✅ [timestamp] nmap-scanner-service - Saludable (X chequeos)
```

### 4.3 Revisar email de recuperación

**Email esperado:**
- ✅ Asunto: "RECUPERADO: nmap-scanner-service"
- Confirmación de restauración, duración del incidente

---

## 📊 PASO 5: Verificar Estado de Todos los Servicios

```bash
docker-compose ps
```

**Deberías ver todos los servicios en estado "Up":**
```
NAME                                              STATUS
quantitative_risk_management-backend-1            Up
quantitative_risk_management-frontend-1           Up
quantitative_risk_management-health-monitor-1     Up
quantitative_risk_management-ml-prediction-...-1  Up
quantitative_risk_management-nmap-scanner-...-1   Up
quantitative_risk_management-nvd-service-1        Up
```

---

## 📸 Evidencia para Documentar

### Captura de pantalla 1: Logs del monitor detectando fallo
```bash
docker-compose logs health-monitor
```

### Captura de pantalla 2: Email de alerta recibido
- Mostrar el email en tu bandeja de entrada

### Captura de pantalla 3: Otros servicios funcionando
```bash
# En una terminal
curl http://localhost:8000/api/v1/health
curl http://localhost:8002/api/v1/health
```

### Captura de pantalla 4: Email de recuperación
- Mostrar el segundo email confirmando recuperación

### Captura de pantalla 5: Estado final de servicios
```bash
docker-compose ps
```

---

## ⏱️ Tiempos Esperados

| Evento | Tiempo |
|--------|--------|
| Detener servicio | Inmediato |
| Primer fallo detectado | ~0 segundos |
| Segundo fallo | ~30 segundos |
| Tercer fallo + Email | ~60 segundos |
| **Total hasta email** | **~90 segundos** |
| Reiniciar servicio | Inmediato |
| Detección de recuperación | ~30 segundos |
| Email de recuperación | ~30 segundos |

---

## ❓ Troubleshooting

### No recibo emails

**Verifica credenciales SMTP en `.env`:**
```bash
SMTP_USER=justingomezcoello@gmail.com
SMTP_PASS=tu_app_password_de_16_caracteres
```

**Revisa logs del monitor:**
```bash
docker-compose logs health-monitor | grep -i "email\|smtp\|error"
```

**Si ves "Error enviando email":**
- Verifica que el `SMTP_PASS` sea el App Password (no tu contraseña normal)
- Verifica que tengas verificación en 2 pasos activada en Gmail
- Revisa la carpeta de SPAM

### El monitor no detecta la caída

**Espera al menos 90 segundos** (3 chequeos × 30 segundos)

**Verifica que el servicio esté realmente detenido:**
```bash
docker-compose ps | grep nmap-scanner
```

---

## 🎯 Resumen de la Prueba

Esta prueba demuestra que:

1. ✅ **Monitoreo funcional**: El health monitor detecta fallos automáticamente
2. ✅ **Notificaciones por email**: Se envían alertas a `justingomezcoello@gmail.com`
3. ✅ **Sistema distribuido resiliente**: Los demás servicios siguen operativos
4. ✅ **Detección de recuperación**: El sistema notifica cuando el servicio vuelve
5. ✅ **Operación 8/5**: El monitor funciona continuamente, notificando a los encargados

**Esto cumple con el requisito de que el proyecto opere 8/5 y notifique cuando un servicio se cae, mientras los demás apartados siguen funcionando.**
