FROM python:3.11-slim

# El directorio de trabajo DENTRO del contenedor
WORKDIR /app

# Instalar psql (cliente de postgres) que es necesario para el script de espera
RUN apt-get update && apt-get install -y postgresql-client && rm -rf /var/lib/apt/lists/*

# Copiar el archivo de requerimientos e instalar las dependencias de Python
# Se copia solo para aprovechar el cache de Docker si no cambia
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el script de espera y hacerlo ejecutable
COPY wait-for-postgres.sh .
RUN chmod +x ./wait-for-postgres.sh

# Copiar todo el código de la aplicación (el contenido de backend/app) al directorio de trabajo
COPY ./app .

# Comando final para ejecutar la aplicación
# 1. Ejecuta el script que espera a postgres
# 2. Inicia uvicorn apuntando a la variable 'app' en el archivo 'main.py'
CMD ["./wait-for-postgres.sh", "db", "python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]