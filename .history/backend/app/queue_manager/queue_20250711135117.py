"""
RabbitMQ Queue Manager for NVD Analysis
"""
import asyncio
import json
import logging
import os
import uuid
from typing import Dict, Any, Optional
import aio_pika
from aio_pika import connect_robust, ExchangeType, Message

logger = logging.getLogger(__name__)

class RabbitMQManager:
    """
    RabbitMQ Manager for handling async NVD analysis jobs
    """
    
    def __init__(self):
        self.connection = None
        self.channel = None
        self.exchange = None
        self.queue = None
        
        # Configuration from environment
        self.rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
        self.queue_name = os.getenv("RABBITMQ_QUEUE", "nvd_analysis_queue")
        self.exchange_name = "nvd_analysis_exchange"
        
    async def connect(self):
        """Establish connection to RabbitMQ"""
        try:
            self.connection = await connect_robust(self.rabbitmq_url)
            self.channel = await self.connection.channel()
            
            # Declare exchange
            self.exchange = await self.channel.declare_exchange(
                self.exchange_name,
                ExchangeType.DIRECT,
                durable=True
            )
            
            # Declare queue
            self.queue = await self.channel.declare_queue(
                self.queue_name,
                durable=True
            )
            
            # Bind queue to exchange
            await self.queue.bind(self.exchange, routing_key="nvd.analysis")
            
            logger.info(f"Connected to RabbitMQ: {self.rabbitmq_url}")
            
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise
    
    async def close(self):
        """Close RabbitMQ connection"""
        try:
            if self.connection and not self.connection.is_closed:
                await self.connection.close()
                logger.info("RabbitMQ connection closed")
        except Exception as e:
            logger.error(f"Error closing RabbitMQ connection: {e}")
    
    async def publish_nvd_analysis(self, job_data: Dict[str, Any]) -> str:
        """
        Publish NVD analysis job to queue
        
        Args:
            job_data: Dictionary containing job information
            
        Returns:
            job_id: Unique identifier for the job
        """
        try:
            # Generate unique job ID
            job_id = str(uuid.uuid4())
            
            # Prepare message
            message_body = {
                "job_id": job_id,
                "timestamp": asyncio.get_event_loop().time(),
                **job_data
            }
            
            # Create message
            message = Message(
                json.dumps(message_body).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                headers={
                    "job_id": job_id,
                    "type": job_data.get("type", "nvd_analysis"),
                    "priority": job_data.get("priority", 1)
                }
            )
            
            # Publish message
            await self.exchange.publish(
                message,
                routing_key="nvd.analysis"
            )
            
            logger.info(f"Published job {job_id} to queue: {job_data.get('keyword', 'unknown')}")
            return job_id
            
        except Exception as e:
            logger.error(f"Failed to publish job to queue: {e}")
            raise
    
    async def get_queue_info(self) -> Dict[str, Any]:
        """
        Get information about the current queue state
        
        Returns:
            Dictionary with queue statistics
        """
        try:
            if not self.queue:
                return {"error": "Not connected to queue"}
            
            # Get queue information using the correct aio_pika API
            queue_info = await self.channel.declare_queue(
                self.queue_name,
                durable=True,
                passive=True  # Only check if queue exists, don't create
            )
            
            return {
                "connected": True,
                "queue_name": self.queue_name,
                "queue_size": queue_info.declaration_result.message_count,
                "consumers": queue_info.declaration_result.consumer_count,
                "total_vulnerabilities": queue_info.declaration_result.message_count,
                "keywords": [],  # Would need to track separately
                "pending": queue_info.declaration_result.message_count,
                "processing": 0,  # Would need separate tracking
                "completed": 0,   # Would need database query
                "failed": 0       # Would need database query
            }
            
        except Exception as e:
            logger.error(f"Failed to get queue info: {e}")
            return {
                "error": str(e),
                "connected": False
            }
    
    async def setup_consumer(self, callback):
        """
        Setup consumer for processing NVD analysis jobs
        This would typically be called by the NVD microservice
        """
        try:
            await self.queue.consume(callback)
            logger.info("Consumer setup completed")
            
        except Exception as e:
            logger.error(f"Failed to setup consumer: {e}")
            raise

# Utility functions for backward compatibility
async def create_rabbitmq_manager() -> RabbitMQManager:
    """Create and connect RabbitMQ manager"""
    manager = RabbitMQManager()
    await manager.connect()
    return manager

async def publish_to_queue(keyword: str, metadata: Dict[str, Any] = None) -> str:
    """
    Simple function to publish a keyword to the analysis queue
    """
    manager = await create_rabbitmq_manager()
    try:
        job_data = {
            "keyword": keyword,
            "type": "single_nvd_search",
            "metadata": metadata or {}
        }
        job_id = await manager.publish_nvd_analysis(job_data)
        return job_id
    finally:
        await manager.close()
