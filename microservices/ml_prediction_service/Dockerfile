FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/

# Set environment variables
ENV PYTHONPATH=/app
ENV CICIDS_MODEL_PATH=/app/src/models/rf_cicids2017_model.pkl
ENV LANL_MODEL_PATH=/app/src/models/isolation_forest_model.pkl

# Expose port
EXPOSE 8001

# Run the application
CMD ["python", "src/main.py"]
