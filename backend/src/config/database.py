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
    import time
    
    max_retries = 5
    retry_delay = 5
    
    for attempt in range(max_retries):
        try:
            # Create SQLAlchemy tables
            Base.metadata.create_all(bind=engine)
            logger.info("PostgreSQL/Supabase database initialization completed")
            return
            
        except Exception as e:
            logger.warning(f"Database initialization attempt {attempt + 1}/{max_retries} failed: {e}")
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                logger.error("All database initialization attempts failed")
                raise


async def close_db():
    """Close database connections"""
    logger.info("Database connections closed")
