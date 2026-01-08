# 🔧 Solución Alternativa - Usar Mailtrap o Servicio de Prueba

## ❌ Problema Actual

Gmail está rechazando la App Password por razones de seguridad. Esto es común y puede ser frustrante.

## ✅ Solución 1: Usar Mailtrap (Recomendado para pruebas)

**Mailtrap** es un servicio gratuito que simula un servidor SMTP y captura todos los emails sin enviarlos realmente. Perfecto para pruebas.

### Pasos:

1. **Regístrate en Mailtrap**: https://mailtrap.io/register/signup
2. **Crea un inbox** (bandeja de prueba)
3. **Copia las credenciales SMTP** que te dan
4. **Actualiza tu `.env`**:

```bash
SMTP_HOST=sandbox.smtp.mailtrap.io
SMTP_PORT=2525
SMTP_USER=tu_usuario_mailtrap
SMTP_PASS=tu_password_mailtrap
```

5. **Reinicia el monitor**:
```bash
docker-compose restart health-monitor
```

6. **Los emails aparecerán en tu inbox de Mailtrap** (no en tu Gmail real)

---

## ✅ Solución 2: Intentar con Outlook/Hotmail

Si prefieres usar un email real, Outlook es más permisivo:

```bash
SMTP_HOST=smtp-mail.outlook.com
SMTP_PORT=587
SMTP_USER=tu_email@outlook.com
SMTP_PASS=tu_contraseña_normal
```

---

## ✅ Solución 3: Verificar App Password de Gmail

Si insistes en usar Gmail, verifica:

1. **Elimina la App Password actual** "Mail" en https://myaccount.google.com/apppasswords
2. **Crea una NUEVA** App Password
3. **Cópiala INMEDIATAMENTE** (sin espacios)
4. **Pégala en `.env`** línea 77
5. **Asegúrate de que NO tenga comillas ni espacios**

---

## 🎯 Recomendación

Para esta demostración, te recomiendo usar **Mailtrap** porque:
- ✅ Es gratis
- ✅ No requiere configuración compleja
- ✅ Funciona al 100%
- ✅ Puedes ver los emails en su interfaz web
- ✅ Perfecto para pruebas y demos

¿Qué solución prefieres probar?
