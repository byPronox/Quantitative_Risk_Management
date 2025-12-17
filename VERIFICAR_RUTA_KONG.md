# 🔍 Verificar y Corregir la Ruta en Kong

## ⚠️ PROBLEMA DETECTADO

Veo en tu imagen que la ruta ya está creada, pero sigue habiendo problemas. Necesitamos verificar algunos detalles.

---

## ✅ PASO 1: Verificar "Strip Path"

En la imagen veo que estás viendo la configuración "Advanced". **Asegúrate de que "Strip Path" esté DESMARCADO**.

1. **Haz clic en la ruta `nvd-database-route`** para editarla
2. Busca el campo **"Strip Path"**
3. **Asegúrate de que NO esté marcado** (checkbox vacío)
4. Si está marcado, **desmárcalo**
5. Haz clic en **"Update"** o **"Actualizar"**

---

## ✅ PASO 2: Verificar que la ruta esté habilitada

1. En la lista de rutas, verifica que `nvd-database-route` tenga un indicador de que está **"Enabled"** o **"Habilitada"**
2. Si no está habilitada, haz clic en ella y busca el toggle para habilitarla

---

## ✅ PASO 3: Verificar el orden de prioridad de rutas

Kong evalúa las rutas en orden. Si tienes:
- `nvd-general-route` con path `/nvd`
- `nvd-database-route` con path `/nvd/database`

La ruta más específica (`/nvd/database`) debería tener **mayor prioridad** (número más alto en "Regex Priority").

1. Ve a la lista de rutas
2. Verifica el campo **"Regex Priority"** de `nvd-database-route`
3. Debería ser **mayor que** el de `nvd-general-route`

---

## ✅ PASO 4: Probar directamente la URL

Abre en tu navegador:
```
https://kong-6abab64110usqnlwd.kongcloud.dev/nvd/database/jobs
```

**Deberías ver:**
- ✅ Un JSON con los jobs (si funciona)
- ❌ El HTML de ngrok (si no funciona)

Si ves el HTML de ngrok, significa que la ruta aún no está funcionando correctamente.

---

## ✅ PASO 5: Verificar en la pestaña "Basic" vs "Advanced"

Cuando edites la ruta:
1. Si estás en modo **"Advanced"**, cambia a modo **"Basic"**
2. En modo Basic, verifica:
   - **Path**: `/nvd/database`
   - **Strip Path**: DESMARCADO
   - **Methods**: GET (marcado)

---

## 🔧 ALTERNATIVA: Si sigue sin funcionar

Si después de verificar todo sigue sin funcionar, intenta:

1. **Borrar la ruta** `nvd-database-route`
2. **Crearla de nuevo** pero esta vez:
   - Usa modo **"Basic"** (no Advanced)
   - Path: `/nvd/database`
   - NO marques "Strip Path"
   - Methods: Solo GET

---

## 📝 RESUMEN DE CONFIGURACIÓN CORRECTA

La ruta `nvd-database-route` debe tener:

```
✅ Name: nvd-database-route
✅ Service: backend-service
✅ Protocols: http, https
✅ Methods: GET
✅ Paths: /nvd/database
❌ Strip Path: DESMARCADO (MUY IMPORTANTE)
✅ Regex Priority: Mayor que otras rutas /nvd
✅ Enabled: Sí
```


