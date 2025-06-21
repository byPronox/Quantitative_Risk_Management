import sys
sys.path.append('/app')

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database.db import Base, engine
from api.routes import router
from api import nvd
import logging

app = FastAPI()

# Set up logging for the app
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("risk_backend")

# Habilita CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # O especifica ["http://localhost:5173"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    logger.info("Creating database tables...")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully.")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")

@app.get("/")
def read_root():
    return {"message": "Backend is running"}

@app.get("/health")
def health_check():
    return {"status": "ok"}

app.include_router(router)
app.include_router(nvd.router)
