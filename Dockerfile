FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y postgresql-client && rm -rf /var/lib/apt/lists/*

# Copiar requerimientos e instalar
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el script de espera y hacerlo ejecutable
COPY backend/wait-for-postgres.sh .
RUN chmod +x ./wait-for-postgres.sh

# Copiar todo el código de la aplicación al directorio de trabajo
COPY backend/app/ .

# Comando de ejecución correcto
CMD ["./wait-for-postgres.sh", "db", "python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"] 