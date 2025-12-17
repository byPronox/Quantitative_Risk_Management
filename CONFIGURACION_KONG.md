# Configuración de Kong Gateway para /nvd/database/*

## Análisis de tu configuración actual

Según las imágenes que compartiste:

### Servicio (backend-service)
- ✅ **Host**: `1d79b7a62dcf.ngrok-free.app` (correcto)
- ✅ **Protocol**: `https` (correcto)
- ✅ **Port**: `443` (correcto)
- ✅ **Enabled**: Sí (correcto)

### Rutas existentes
1. `backend-route` - Path: `/` (debería capturar todo)
2. `nvd-general-route` - Path: `/nvd` (captura `/nvd/*` pero puede tener conflictos)
3. `api-v1-route` - Path: `/api/v1`
4. `nvd-async-route` - Path: `/nvd/analyze_software_async`

## Problema identificado

El error `ERR_NGROK_6024` indica que ngrok está interceptando las peticiones del navegador y mostrando su página de advertencia en lugar de pasarlas al backend.

## Solución implementada

He modificado el frontend para que **use directamente `http://localhost:8000` cuando estás en desarrollo local**, evitando pasar por Kong/ngrok. Esto soluciona el problema inmediatamente.

## Si quieres usar Kong en desarrollo (opcional)

Si realmente necesitas usar Kong incluso en desarrollo local, tendrías que:

### Opción 1: Agregar ruta específica en Kong
Crear una nueva ruta `nvd-database-route`:
- **Service**: `backend-service`
- **Path**: `/nvd/database`
- **Methods**: `GET`
- **Protocols**: `http`, `https`

### Opción 2: Configurar ngrok para omitir warnings
Ejecutar ngrok con:
```bash
ngrok http 8000 --request-header-add="ngrok-skip-browser-warning:true"
```

Pero esto requiere modificar cómo ejecutas ngrok.

## Recomendación

**La solución actual (usar localhost directamente en desarrollo) es la mejor opción** porque:
- ✅ Funciona inmediatamente sin cambios en Kong
- ✅ Más rápido (sin pasar por ngrok)
- ✅ Sin problemas de CORS o warnings de ngrok
- ✅ En producción seguirá usando Kong si lo configuras

En producción, cuando despliegues, simplemente configura las variables de entorno `VITE_API_URL` y `VITE_BACKEND_URL` para que apunten a Kong.

