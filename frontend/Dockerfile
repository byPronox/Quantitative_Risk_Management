FROM node:20-alpine AS build

WORKDIR /app

# Copia solo lo necesario para instalar dependencias primero
COPY package.json package-lock.json ./
RUN npm install

# Luego copia el resto del código
COPY . .

# Construye el proyecto
RUN npm run build

# Etapa de producción
FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
