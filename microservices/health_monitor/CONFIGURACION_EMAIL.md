# 📧 Configuración de Email para Health Monitor

## ⚠️ IMPORTANTE: Configurar antes de usar

El servicio de monitoreo necesita credenciales SMTP para enviar notificaciones por email. Sigue estos pasos:

---

## 🔐 Paso 1: Crear App Password de Gmail

### Opción A: Si tienes verificación en 2 pasos activada

1. **Ve a tu cuenta de Google**: https://myaccount.google.com/security
2. **Busca "App passwords"** (Contraseñas de aplicaciones)
3. **Genera una nueva contraseña**:
   - Nombre: "QRM Health Monitor"
   - Tipo: "Mail"
4. **Copia la contraseña** de 16 caracteres (formato: `xxxx xxxx xxxx xxxx`)

### Opción B: Si NO tienes verificación en 2 pasos

1. **Activa la verificación en 2 pasos primero**:
   - Ve a https://myaccount.google.com/security
   - Busca "2-Step Verification" y actívala
   - Sigue el proceso de configuración
2. **Luego sigue la Opción A**

---

## ⚙️ Paso 2: Configurar credenciales en `.env`

Abre el archivo `.env` y actualiza estas líneas:

```bash
# Cambia estos valores:
SMTP_USER=tu_email@gmail.com          # ← Tu email de Gmail
SMTP_PASS=xxxx xxxx xxxx xxxx         # ← App Password de 16 caracteres
```

**Ejemplo**:
```bash
SMTP_USER=fabrikfaf@gmail.com
SMTP_PASS=abcd efgh ijkl mnop
```

---

## 🚀 Paso 3: Reiniciar el servicio

Después de configurar las credenciales:

```bash
docker-compose restart health-monitor
```

---

## ✅ Paso 4: Verificar que funciona

### Ver logs del monitor:
```bash
docker-compose logs -f health-monitor
```

**Deberías ver**:
```
✅ Configuración de email verificada
✅ [timestamp] nmap-scanner-service - Saludable (X chequeos)
```

**Si ves advertencia**:
```
⚠️  ADVERTENCIA: Credenciales SMTP no configuradas
```
→ Verifica que actualizaste correctamente `SMTP_USER` y `SMTP_PASS` en `.env`

---

## 🧪 Paso 5: Probar notificaciones (Simulación)

### 1. Detener el servicio nmap-scanner:
```bash
docker-compose stop nmap-scanner-service
```

### 2. Observar logs del monitor:
```bash
docker-compose logs -f health-monitor
```

**Verás**:
```
❌ [timestamp] nmap-scanner-service - Fallo 1/3
❌ [timestamp] nmap-scanner-service - Fallo 2/3
❌ [timestamp] nmap-scanner-service - Fallo 3/3
🚨 ALERTA: Enviando notificación de fallo...
✅ Email enviado: <message-id>
```

### 3. Revisar tu email (fabrikfaf@gmail.com):
Deberías recibir un email con:
- **Asunto**: 🚨 ALERTA: nmap-scanner-service CAÍDO
- **Contenido**: Detalles del incidente, timestamp, comandos recomendados

### 4. Reiniciar el servicio:
```bash
docker-compose start nmap-scanner-service
```

**Verás**:
```
✅ RECUPERACIÓN: Servicio restaurado
✅ Email enviado: <message-id>
```

### 5. Revisar email de recuperación:
- **Asunto**: ✅ RECUPERADO: nmap-scanner-service

---

## 🔧 Troubleshooting

### ❌ "Error enviando email: Invalid login"
- Verifica que el `SMTP_USER` sea correcto
- Verifica que el `SMTP_PASS` sea el App Password (no tu contraseña normal)
- Asegúrate de que no haya espacios extra en las credenciales

### ❌ "Error enviando email: Connection timeout"
- Verifica tu conexión a internet
- Verifica que el puerto 587 no esté bloqueado por firewall

### ❌ No recibo emails
- Revisa la carpeta de SPAM
- Verifica que `ALERT_EMAIL=fabrikfaf@gmail.com` esté correcto
- Revisa los logs: `docker-compose logs health-monitor`

---

## ⏱️ Configuración de Intervalos

### Modo Simulación (actual):
```bash
HEALTH_CHECK_INTERVAL_MS=30000  # 30 segundos
```

### Modo Producción:
```bash
HEALTH_CHECK_INTERVAL_MS=1800000  # 30 minutos
```

Después de cambiar, reinicia:
```bash
docker-compose restart health-monitor
```

---

## 📊 Estado del Sistema

### Ver todos los servicios:
```bash
docker-compose ps
```

### Ver logs de todos los servicios:
```bash
docker-compose logs -f
```

### Detener todo:
```bash
docker-compose down
```

### Iniciar todo:
```bash
docker-compose up -d
```
