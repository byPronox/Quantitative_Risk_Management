# Etapa 1: build de React
FROM node:20-alpine AS build

WORKDIR /app

# Instala Vite de forma global (¡importante!)
RUN npm install -g vite

# Copiar archivos de configuración primero para cacheo
COPY ./frontend/package*.json ./
COPY ./frontend/vite.config.* ./

# Instalar dependencias (incluye devDependencies)
RUN npm install

# Copiar el resto de los archivos del frontend
COPY ./frontend .

# Compilar el proyecto
RUN npm run build

# Etapa 2: servir con Nginx
FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
