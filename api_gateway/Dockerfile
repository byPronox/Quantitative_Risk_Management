FROM python:3.11-slim

WORKDIR /app

COPY api_gateway.py /app/api_gateway.py
RUN pip install fastapi uvicorn httpx

CMD ["uvicorn", "api_gateway:app", "--host", "0.0.0.0", "--port", "8000"]