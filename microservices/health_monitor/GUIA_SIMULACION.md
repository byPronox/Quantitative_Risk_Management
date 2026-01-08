# 🧪 Guía de Simulación - Health Monitor

## 📋 Resumen del Sistema

El **Health Monitor** está configurado para:
- ✅ Monitorear `nmap-scanner-service` cada **30 segundos**
- ✅ Detectar fallos después de **3 intentos consecutivos** (~90 segundos)
- ✅ Enviar emails a: **fabrikfaf@gmail.com**
- ✅ Notificar tanto caídas como recuperaciones

---

## 🎯 Simulación de Caída del Servicio

### Paso 1: Verificar que el monitor está funcionando

```bash
docker-compose logs --tail=20 health-monitor
```

**Deberías ver**:
```
✅ [timestamp] nmap-scanner-service - Saludable (X chequeos)
```

---

### Paso 2: Detener el servicio nmap-scanner

```bash
docker-compose stop nmap-scanner-service
```

**Esto simula que el servicio se cayó** (por ejemplo, por un error, falta de recursos, etc.)

---

### Paso 3: Observar la detección del fallo

```bash
docker-compose logs -f health-monitor
```

**Verás la siguiente secuencia** (~90 segundos total):

```
🔍 Ejecutando chequeo de salud...
❌ [timestamp] nmap-scanner-service - Fallo 1/3
   Error: connect ECONNREFUSED 172.x.x.x:8004

🔍 Ejecutando chequeo de salud...
❌ [timestamp] nmap-scanner-service - Fallo 2/3
   Error: connect ECONNREFUSED 172.x.x.x:8004

🔍 Ejecutando chequeo de salud...
❌ [timestamp] nmap-scanner-service - Fallo 3/3
   Error: connect ECONNREFUSED 172.x.x.x:8004

🚨 ALERTA: Enviando notificación de fallo...
✅ Email enviado: <message-id>
```

---

### Paso 4: Revisar el email de alerta

1. **Abre tu correo**: fabrikfaf@gmail.com
2. **Busca el email** (puede tardar 1-2 minutos)
3. **Revisa también SPAM** si no aparece en la bandeja principal

**El email contendrá**:
- 🚨 **Asunto**: "ALERTA: nmap-scanner-service CAÍDO"
- 📊 **Detalles**: Timestamp, número de fallos, error específico
- 🔧 **Acciones recomendadas**: Comandos para diagnosticar y resolver

---

## ✅ Simulación de Recuperación

### Paso 5: Reiniciar el servicio

```bash
docker-compose start nmap-scanner-service
```

---

### Paso 6: Observar la detección de recuperación

```bash
docker-compose logs -f health-monitor
```

**Verás**:
```
🔍 Ejecutando chequeo de salud...
✅ RECUPERACIÓN: Servicio restaurado
✅ Email enviado: <message-id>
✅ [timestamp] nmap-scanner-service - Saludable (X chequeos)
```

---

### Paso 7: Revisar el email de recuperación

**El email contendrá**:
- ✅ **Asunto**: "RECUPERADO: nmap-scanner-service"
- 🎉 **Mensaje**: Confirmación de que el servicio está operativo
- ⏱️ **Duración**: Tiempo que estuvo caído

---

## 🔍 Verificar Independencia de Servicios

Mientras `nmap-scanner-service` está detenido, verifica que los otros servicios siguen funcionando:

### Backend:
```bash
curl http://localhost:8000/api/v1/health
```

### NVD Service:
```bash
curl http://localhost:8002/api/v1/health
```

### Frontend:
Abre en el navegador: http://localhost:5173

**Resultado esperado**: ✅ Todos los demás servicios responden correctamente

---

## 📊 Comandos Útiles

### Ver estado de todos los contenedores:
```bash
docker-compose ps
```

### Ver logs de todos los servicios:
```bash
docker-compose logs -f
```

### Ver solo logs del monitor:
```bash
docker-compose logs -f health-monitor
```

### Ver solo logs del nmap-scanner:
```bash
docker-compose logs -f nmap-scanner-service
```

### Reiniciar solo el monitor:
```bash
docker-compose restart health-monitor
```

---

## ⚙️ Configuración Actual

```bash
# Intervalo de chequeo
HEALTH_CHECK_INTERVAL_MS=30000  # 30 segundos (SIMULACIÓN)

# Email destino
ALERT_EMAIL=fabrikfaf@gmail.com

# Reintentos antes de alerta
MAX_RETRIES=3  # ~90 segundos total
```

---

## 🚀 Cambiar a Modo Producción

Cuando termines las pruebas, actualiza `.env`:

```bash
# Cambiar de 30 segundos a 30 minutos
HEALTH_CHECK_INTERVAL_MS=1800000
```

Luego reinicia:
```bash
docker-compose restart health-monitor
```

---

## ❓ Troubleshooting

### No recibo emails

1. **Verifica credenciales SMTP** en `.env`:
   ```bash
   SMTP_USER=tu_email@gmail.com
   SMTP_PASS=tu_app_password
   ```

2. **Revisa logs del monitor**:
   ```bash
   docker-compose logs health-monitor | grep -i "email\|smtp\|error"
   ```

3. **Verifica la carpeta de SPAM**

### El monitor no detecta la caída

1. **Verifica que el servicio esté realmente detenido**:
   ```bash
   docker-compose ps | grep nmap-scanner
   ```

2. **Espera al menos 90 segundos** (3 chequeos × 30 segundos)

### El servicio se reinicia automáticamente

Docker Compose tiene `restart: always`. Para simular una caída permanente:
```bash
docker-compose stop nmap-scanner-service
```

NO uses `docker-compose restart` porque lo reiniciará automáticamente.

---

## 📝 Notas Importantes

- ⏱️ **Tiempo de detección**: ~90 segundos (3 fallos × 30 segundos)
- 📧 **Emails**: Se envían tanto para caídas como para recuperaciones
- 🔄 **Independencia**: Los demás servicios siguen funcionando
- 🛡️ **Producción**: Cambia el intervalo a 30 minutos después de las pruebas
