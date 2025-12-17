# 📋 Pasos para Aplicar los Cambios

## Opción 1: Reiniciar Servicios (Más Rápido)

Como tienes volúmenes montados, los cambios en código ya están en los contenedores, solo necesitas reiniciar:

```bash
# Reiniciar backend y nvd-service
docker-compose restart backend nvd-service

# Reconstruir frontend (necesario porque es build estático)
docker-compose build frontend
docker-compose up -d frontend
```

## Opción 2: Reconstruir Todo (Más Seguro)

Si quieres asegurarte de que todo esté actualizado:

```bash
# Reconstruir solo los servicios modificados
docker-compose build backend nvd-service frontend

# Reiniciar los servicios
docker-compose up -d backend nvd-service frontend
```

## Opción 3: Reinicio Completo (Si hay problemas)

```bash
# Detener todo
docker-compose down

# Reconstruir las imágenes modificadas
docker-compose build backend nvd-service frontend

# Iniciar todo de nuevo
docker-compose up -d
```

## Verificar que los cambios funcionen

1. Verifica los logs del backend:
```bash
docker-compose logs -f backend
```

2. Verifica los logs del nvd-service:
```bash
docker-compose logs -f nvd-service
```

3. Verifica que los endpoints funcionen:
```bash
# Probar endpoint de jobs
curl http://localhost:8000/nvd/database/jobs

# Probar endpoint de vulnerabilidades  
curl http://localhost:8000/nvd/database/vulnerabilities?limit=10
```

4. Abre el frontend en el navegador:
```
http://localhost:5173/reports
```

## Nota sobre ngrok

Como estás usando ngrok en el puerto 8000, después de reiniciar, asegúrate de que ngrok siga corriendo y apuntando al puerto correcto.

