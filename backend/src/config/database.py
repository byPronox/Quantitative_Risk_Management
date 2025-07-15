"""
Database configuration and initialization
"""
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient

from .settings import settings

logger = logging.getLogger(__name__)

# SQLAlchemy setup
Base = declarative_base()

# Synchronous engine for compatibility
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# MongoDB setup
mongodb_client: AsyncIOMotorClient = None
mongodb_database = None


def get_db() -> Session:
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_mongodb():
    """Get MongoDB database instance"""
    return mongodb_database


async def init_db():
    """Initialize database connections"""
    global mongodb_client, mongodb_database
    
    try:
        # Initialize MongoDB
        mongodb_client = AsyncIOMotorClient(settings.MONGODB_URL)
        mongodb_database = mongodb_client[settings.MONGODB_DATABASE]
        
        # Test MongoDB connection
        await mongodb_client.admin.command('ismaster')
        logger.info("MongoDB connection established")
        
        # Create SQLAlchemy tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialization completed")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise


async def close_db():
    """Close database connections"""
    global mongodb_client
    
    if mongodb_client:
        mongodb_client.close()
        logger.info("Database connections closed")
