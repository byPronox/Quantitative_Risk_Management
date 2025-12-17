# 📝 Cómo Llenar el Formulario de Kong

## ✅ Campos que ya tienes bien:
- ✅ **Name**: `nvd-database-route` (perfecto)
- ✅ **Service**: `backend-service` (perfecto)
- ✅ **Tags**: Puede quedar vacío (no es necesario)

## ⚠️ Campos que necesitas cambiar:

### 1️⃣ **Path** (CAMPO VACÍO - LLENAR ESTO)
```
/nvd/database
```
**Escribe exactamente esto:** `/nvd/database`

---

### 2️⃣ **Strip Path** (ESTÁ MARCADO - DESMARCAR ESTO)
- ❌ **QUITA la marca del checkbox "Strip Path"**
- **¿Por qué?** Si está marcado, Kong quita el path antes de enviarlo al backend, y tu backend necesita recibir `/nvd/database/jobs` completo

---

### 3️⃣ **Methods** (YA TIENES GET - ESTÁ BIEN)
- ✅ Deja **GET** marcado (necesario)
- ⚠️ **POST** puedes quitarlo si quieres (no es necesario, pero tampoco molesta)

---

### 4️⃣ **Host** (VACÍO - PERFECTO)
- ✅ Déjalo vacío (así está bien)

---

## 📋 RESUMEN - Así debe quedar:

```
Name: nvd-database-route                    ✅ (ya lo tienes)

Service: backend-service                    ✅ (ya lo tienes)

Tags: (vacío)                               ✅ (puede quedar vacío)

Path: /nvd/database                         ⚠️ LLENAR ESTO

Strip Path: [ ] DESMARCAR                   ⚠️ QUITAR MARCA

Methods: 
  ☑ GET                                     ✅ (está bien)
  ☐ POST (opcional - puedes quitarlo)       ⚠️ OPCIONAL

Host: (vacío)                               ✅ (perfecto)
```

---

## 🎯 PASOS:

1. **En el campo "Path"**, escribe: `/nvd/database`
2. **Quita la marca** del checkbox "Strip Path"
3. (Opcional) Si quieres, quita POST de Methods, pero no es necesario
4. Haz clic en **"Create"** o **"Crear"**

---

## ⚠️ IMPORTANTE - Strip Path:

Si "Strip Path" está marcado:
- ❌ Kong quita `/nvd/database` antes de enviar al backend
- ❌ Tu backend recibe solo `/jobs` en lugar de `/nvd/database/jobs`
- ❌ No funcionará

Si "Strip Path" está DESMARCADO (como debe ser):
- ✅ Kong envía el path completo al backend
- ✅ Tu backend recibe `/nvd/database/jobs` completo
- ✅ Funcionará correctamente

