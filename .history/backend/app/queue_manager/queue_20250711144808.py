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

# Simple in-memory job storage (in production, use Redis or database)
_job_metadata_store = {}

def store_job_metadata(job_id: str, metadata: Dict[str, Any]):
    """Store job metadata for later retrieval"""
    _job_metadata_store[job_id] = metadata

def get_stored_job_metadata(job_id: str) -> Dict[str, Any]:
    """Retrieve stored job metadata"""
    return _job_metadata_store.get(job_id, {})

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
            
            # Store job metadata
            store_job_metadata(job_id, job_data)
            
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
            # Check connection status
            if not self.connection or self.connection.is_closed:
                return {
                    "error": "Not connected to RabbitMQ",
                    "connected": False,
                    "queue_size": 0,
                    "total_vulnerabilities": 0,
                    "keywords": [],
                    "status": "disconnected"
                }
            
            # Return basic queue info (simplified for now)
            return {
                "connected": True,
                "queue_name": self.queue_name,
                "queue_size": 0,  # Simplified - would need proper inspection
                "total_vulnerabilities": 0,
                "keywords": [],
                "pending": 0,
                "processing": 0,
                "completed": 0,
                "failed": 0,
                "status": "connected"
            }
            
        except Exception as e:
            logger.error(f"Failed to get queue info: {e}")
            return {
                "error": str(e),
                "connected": False,
                "queue_size": 0,
                "total_vulnerabilities": 0,
                "keywords": [],
                "status": "error"
            }
    
    async def setup_consumer(self, callback):
        """
        Setup consumer for processing NVD analysis jobs
        This would typically be called by the NVD microservice
        """
        try:
            if not self.queue:
                raise Exception("Queue not initialized")
            await self.queue.consume(callback)
            logger.info("Consumer setup completed")
            
        except Exception as e:
            logger.error(f"Failed to setup consumer: {e}")
            raise
    
    async def get_job_metadata(self, job_id: str) -> Dict[str, Any]:
        """
        Get metadata for a specific job ID
        
        Args:
            job_id: The job ID to look up
            
        Returns:
            Dictionary with job metadata or None if not found
        """
        try:
            if not self.connection or self.connection.is_closed:
                await self.connect()
            
            if not self.channel:
                logger.error("No channel available for job metadata lookup")
                return {}
            
            # Retrieve job metadata from storage
            metadata = get_stored_job_metadata(job_id)
            if metadata:
                return {
                    "job_id": job_id,
                    "keyword": metadata.get("keyword", "vulnerability"),
                    "status": "processing"
                }
            
            return {}
            
        except Exception as e:
            logger.error(f"Failed to get job metadata for {job_id}: {e}")
            return {}

# Utility functions for backward compatibility
async def create_rabbitmq_manager() -> RabbitMQManager:
    """Create and connect RabbitMQ manager"""
    manager = RabbitMQManager()
    await manager.connect()
    return manager

async def publish_to_queue(keyword: str, metadata: Dict[str, Any] | None = None) -> str:
    """
    Simple function to publish a keyword to the analysis queue
    """
    try:
        manager = RabbitMQManager()
        await manager.connect()
        
        job_data = {
            "keyword": keyword,
            "type": "single_nvd_search",
            "metadata": metadata or {}
        }
        job_id = await manager.publish_nvd_analysis(job_data)
        await manager.close()
        return job_id
        
    except Exception as e:
        logger.error(f"Failed to publish to queue: {e}")
        # Return a mock job ID if RabbitMQ is unavailable
        return f"mock-job-{uuid.uuid4()}"
