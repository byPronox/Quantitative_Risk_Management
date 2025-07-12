# 🚀 Kong Gateway Setup Guide

## 📋 Configuración Actual

Tu Kong Gateway ya está configurado en Konnect con:

- **Proxy URL**: `https://kong-b27b67aff4usnspl9.kongcloud.dev`
- **Control Plane ID**: `9d98c0ba-3ac1-44fd-b497-59743e18a80a`
- **Admin API**: `https://us.api.konghq.com/v2/control-planes/9d98c0ba-3ac1-44fd-b497-59743e18a80a`

## 🔑 Pasos para obtener Personal Access Token

1. **Accede a Kong Konnect**:
   - Ve a https://cloud.konghq.com/
   - Inicia sesión con tu cuenta

2. **Crear Personal Access Token**:
   - Ve a **Settings** → **Personal Access Tokens**
   - Click en **Generate Token**
   - Asigna un nombre: `quantitative-risk-backend`
   - Selecciona los scopes necesarios:
     - `services:write`
     - `routes:write`
     - `control-planes:read`
   - Copia el token generado

3. **Configurar el Token**:
   - Edita el archivo `.env`
   - Reemplaza `KONG_TOKEN=` con `KONG_TOKEN=tu_token_aqui`

## 🐳 Ejecutar el Sistema

1. **Con Docker Compose**:
   ```bash
   # Ejecutar como administrador en PowerShell
   docker-compose up --build
   ```

2. **Verificar Servicios**:
   - **Backend**: http://localhost:8000
   - **Frontend**: http://localhost:5173
   - **RabbitMQ Management**: http://localhost:15672 (guest/guest)
   - **PostgreSQL**: localhost:5432

3. **Kong Gateway**:
   - **Proxy**: https://kong-b27b67aff4usnspl9.kongcloud.dev
   - El backend se registrará automáticamente en Kong al iniciar

## 🔄 Arquitectura Final

```
Frontend (React) 
    ↓
Kong Gateway (Konnect)
    ↓
Backend (FastAPI)
    ↓
┌─────────────────┬─────────────────┐
│   PostgreSQL    │    RabbitMQ     │
│   (Database)    │   (NVD Queue)   │
└─────────────────┴─────────────────┘
```

## 📊 Funcionalidades con RabbitMQ

- ✅ **Análisis NVD**: Cola de vulnerabilidades para análisis diferido
- ✅ **Queue Management**: Agregar/limpiar cola de análisis
- ✅ **Enterprise Metrics**: Análisis empresarial basado en cola
- ✅ **ML Predictions**: Logging asíncrono de predicciones

## 🔧 Troubleshooting

Si Kong Gateway no se registra automáticamente:
1. Verifica que `KONG_TOKEN` esté configurado en `.env`
2. Revisa los logs del backend: `docker-compose logs backend`
3. El sistema funcionará normalmente sin Kong, solo sin el proxy

## 🎯 URLs de Acceso

- **Desarrollo Local**: http://localhost:5173 → http://localhost:8000
- **Producción con Kong**: http://localhost:5173 → https://kong-b27b67aff4usnspl9.kongcloud.dev
