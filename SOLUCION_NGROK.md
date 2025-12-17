# Solución al Error ERR_NGROK_6024

## Problema
Ngrok está interceptando las peticiones del frontend y mostrando su página de advertencia en lugar de pasarlas al backend.

## Soluciones

### Opción 1: Usar localhost directamente en desarrollo (RECOMENDADO)
Cambiar el frontend para que use `http://localhost:8000` directamente en desarrollo, evitando ngrok.

### Opción 2: Agregar ruta en Kong
Crear una ruta específica en Kong para `/nvd/database/*` que apunte al `backend-service`.

### Opción 3: Configurar ngrok con headers
Ejecutar ngrok con la opción para omitir la página de advertencia.


