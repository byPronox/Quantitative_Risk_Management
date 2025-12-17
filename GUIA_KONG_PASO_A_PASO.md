# 🎯 Guía Paso a Paso: Configurar Kong para /nvd/database/*

## 📋 RESUMEN DEL PROBLEMA

Ngrok está bloqueando las peticiones porque Kong **NO tiene una ruta configurada** para `/nvd/database/*`.

## ✅ LO QUE YA TIENES BIEN

Según las imágenes que compartiste:

### 1. Servicio `backend-service` ✅
- **Host**: `1d79b7a62dcf.ngrok-free.app` ✅
- **Protocol**: `https` ✅
- **Port**: `443` ✅
- **Enabled**: Sí ✅

### 2. Rutas existentes:
- `backend-route` - Path: `/` (captura todo lo demás)
- `nvd-general-route` - Path: `/nvd` (pero NO captura `/nvd/database/*`)
- `api-v1-route` - Path: `/api/v1`
- `nvd-async-route` - Path: `/nvd/analyze_software_async`

## ❌ LO QUE TE FALTA

**Necesitas crear UNA NUEVA RUTA en Kong** para que las peticiones a `/nvd/database/*` lleguen al backend.

---

## 🔧 PASOS PARA CREAR LA RUTA EN KONG

### PASO 1: Ir a Kong Admin

1. Abre tu navegador
2. Ve a tu panel de Kong (donde viste las rutas)
3. En el menú lateral, busca **"Routes"** o **"Rutas"**
4. Haz clic en el botón azul **"+ New route"** o **"Nueva ruta"**

---

### PASO 2: Configurar la Nueva Ruta

En el formulario que aparece, completa estos campos:

#### 📌 **Name** (Nombre)
```
nvd-database-route
```
*(Puedes ponerle cualquier nombre que quieras, esto es solo para identificarla)*

#### 📌 **Service** (Servicio)
```
backend-service
```
*(Selecciona el servicio `backend-service` del dropdown)*

#### 📌 **Protocols** (Protocolos)
- ✅ Marca `http`
- ✅ Marca `https`

#### 📌 **Methods** (Métodos HTTP)
- ✅ Marca `GET`
- *(Opcionalmente también `POST` si vas a necesitarlo)*

#### 📌 **Paths** (Rutas - **ESTE ES EL MÁS IMPORTANTE**)
Agrega estas rutas:
```
/nvd/database/jobs
/nvd/database/vulnerabilities
```

**IMPORTANTE:** 
- Puedes agregar múltiples paths
- O puedes usar un path con wildcard: `/nvd/database` (esto captura `/nvd/database/*`)

**Opciones:**
- **Opción A (Específica)**: Agrega cada path individualmente:
  - Path 1: `/nvd/database/jobs`
  - Path 2: `/nvd/database/vulnerabilities`
  
- **Opción B (Wildcard - RECOMENDADO)**: Agrega un solo path:
  - Path: `/nvd/database`
  - Esto capturará TODAS las rutas que empiecen con `/nvd/database/`

#### 📌 **Strip Path** (Opcional)
Deja esto en **NO** o **false** (no marcar)

#### 📌 **Preserve Host** (Opcional)
Deja esto como está (por defecto está bien)

---

### PASO 3: Guardar la Ruta

1. Haz clic en el botón **"Create"** o **"Crear"** (generalmente está abajo)
2. Verifica que la ruta aparezca en tu lista de rutas

---

## 📊 VERIFICACIÓN

Después de crear la ruta, deberías ver en tu lista de rutas:

```
Name: nvd-database-route
Service: backend-service
Protocols: http, https
Methods: GET
Paths: /nvd/database (o los paths que hayas puesto)
```

---

## 🎯 RUTAS QUE DEBES TENER EN TOTAL

Después de agregar la nueva ruta, deberías tener estas rutas:

1. ✅ `backend-route` - Path: `/`
2. ✅ `nvd-general-route` - Path: `/nvd`
3. ✅ `api-v1-route` - Path: `/api/v1`
4. ✅ `nvd-async-route` - Path: `/nvd/analyze_software_async`
5. ✅ **`nvd-database-route`** - Path: `/nvd/database` ⭐ **NUEVA**

---

## 🧪 PROBAR QUE FUNCIONA

Después de crear la ruta:

1. Recarga tu página de reportes en el navegador
2. Abre la consola del navegador (F12)
3. Deberías ver que ahora las peticiones van a través de Kong y no aparecen errores de ngrok

Si todavía ves el error de ngrok, puede ser que necesites:
- Esperar unos segundos para que Kong actualice la configuración
- Verificar que la ruta esté habilitada (Enabled: Yes)

---

## ❓ PREGUNTAS FRECUENTES

**P: ¿Por qué necesito esta ruta si ya tengo `backend-route` con path `/`?**
R: Porque Kong evalúa las rutas en orden de especificidad. La ruta `/nvd/database` es más específica que `/`, así que Kong la procesará primero.

**P: ¿Qué pasa si tengo conflicto entre rutas?**
R: Kong usa la ruta más específica primero. Si tienes `/nvd` y `/nvd/database`, la segunda será más específica y se usará para rutas que empiecen con `/nvd/database`.

**P: ¿Debo quitar alguna ruta existente?**
R: No, déjalas todas. La nueva ruta solo complementa las existentes.

---

## 🔍 SI SIGUE SIN FUNCIONAR

Si después de crear la ruta sigue sin funcionar:

1. Verifica que el servicio `backend-service` esté habilitado (Enabled: Yes)
2. Verifica que la nueva ruta esté habilitada
3. Verifica que ngrok siga corriendo: `ngrok http 8000`
4. Prueba hacer una petición directa desde el navegador:
   - Ve a: `https://kong-6abab64110usqnlwd.kongcloud.dev/nvd/database/jobs`
   - Deberías ver un JSON con los jobs (o un error de autenticación, pero NO el HTML de ngrok)


