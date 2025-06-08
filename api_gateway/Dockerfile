FROM python:3.11-slim

WORKDIR /app

COPY ./main.py /app/main.py
COPY ./config /app/config
COPY ./interfaces /app/interfaces
COPY ./services /app/services

RUN pip install fastapi uvicorn httpx

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]