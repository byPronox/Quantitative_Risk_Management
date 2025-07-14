from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class MongoDBConnection:
    client: AsyncIOMotorClient = None
    database = None

    @classmethod
    async def connect(cls):
        """Create database connection"""
        try:
            cls.client = AsyncIOMotorClient(settings.MONGODB_URL)
            cls.database = cls.client[settings.MONGODB_DATABASE]
            
            # Test connection
            await cls.client.admin.command('ping')
            logger.info(f"Connected to MongoDB database: {settings.MONGODB_DATABASE}")
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    @classmethod
    async def disconnect(cls):
        """Close database connection"""
        if cls.client:
            cls.client.close()
            logger.info("Disconnected from MongoDB")

    @classmethod
    def get_database(cls):
        """Get database instance"""
        return cls.database
