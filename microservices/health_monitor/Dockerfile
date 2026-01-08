FROM node:18-alpine

WORKDIR /app

# Copiar package files
COPY package*.json ./

# Instalar dependencias
RUN npm install --production

# Copiar código fuente
COPY src/ ./src/

# Exponer puerto (opcional, este servicio no tiene API)
# EXPOSE 8005

# Comando de inicio
CMD ["npm", "start"]
