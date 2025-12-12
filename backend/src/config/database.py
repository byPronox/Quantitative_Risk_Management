"""
Database configuration and initialization
Uses PostgreSQL/Supabase as the single database
"""
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from .settings import settings

logger = logging.getLogger(__name__)

# SQLAlchemy setup
Base = declarative_base()

# Synchronous engine for compatibility
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def init_db():
    """Initialize database connections"""
    try:
        # Create SQLAlchemy tables
        Base.metadata.create_all(bind=engine)
        logger.info("PostgreSQL/Supabase database initialization completed")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise


async def close_db():
    """Close database connections"""
    logger.info("Database connections closed")
