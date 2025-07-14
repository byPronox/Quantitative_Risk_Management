"""
MongoDB connection and client management.
Handles connection to MongoDB Atlas and provides database instance.
"""
import logging
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure
from config.config import Settings

# Create settings instance
settings = Settings()

logger = logging.getLogger(__name__)

class MongoDBConnection:
    """MongoDB connection manager using Motor for async operations."""
    
    _client: Optional[AsyncIOMotorClient] = None
    _database: Optional[AsyncIOMotorDatabase] = None
    
    @classmethod
    async def connect(cls) -> None:
        """Establish connection to MongoDB Atlas."""
        try:
            cls._client = AsyncIOMotorClient(
                settings.MONGODB_URL,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
                socketTimeoutMS=5000
            )
            
            # Test the connection
            await cls._client.admin.command('ping')
            cls._database = cls._client[settings.MONGODB_DATABASE]
            logger.info(f"Successfully connected to MongoDB database: {settings.MONGODB_DATABASE}")
            
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error connecting to MongoDB: {e}")
            raise
    
    @classmethod
    async def disconnect(cls) -> None:
        """Close MongoDB connection."""
        if cls._client:
            cls._client.close()
            cls._client = None
            cls._database = None
            logger.info("MongoDB connection closed")
    
    @classmethod
    def get_database(cls) -> AsyncIOMotorDatabase:
        """Get the MongoDB database instance."""
        if cls._database is None:
            raise RuntimeError("MongoDB not connected. Call connect() first.")
        return cls._database
    
    @property
    def db(self) -> AsyncIOMotorDatabase:
        """Property to access database directly for backward compatibility."""
        return self.get_database()
    
    @classmethod
    def get_client(cls) -> AsyncIOMotorClient:
        """Get the MongoDB client instance."""
        if cls._client is None:
            raise RuntimeError("MongoDB not connected. Call connect() first.")
        return cls._client

# Convenience function to get database
async def get_mongodb() -> AsyncIOMotorDatabase:
    """Get MongoDB database instance."""
    return MongoDBConnection.get_database()
