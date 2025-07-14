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
import httpx
from datetime import datetime
from ..database.mongodb_connection import MongoDBConnection

logger = logging.getLogger(__name__)

# Simple in-memory job storage (in production, use Redis or database)
_job_metadata_store = {}
_job_results_store = {}  # Store completed job results

# MongoDB instance for storing vulnerability results
_mongodb_instance = None

async def get_mongodb_instance():
    """Get MongoDB instance for storing vulnerability results"""
    global _mongodb_instance
    if _mongodb_instance is None:
        _mongodb_instance = MongoDBConnection()
        await _mongodb_instance.connect()
    return _mongodb_instance

def store_job_metadata(job_id: str, metadata: Dict[str, Any]):
    """Store job metadata for later retrieval"""
    _job_metadata_store[job_id] = metadata

def get_stored_job_metadata(job_id: str) -> Dict[str, Any]:
    """Retrieve stored job metadata"""
    return _job_metadata_store.get(job_id, {})

async def store_job_result(job_id: str, result: Dict[str, Any]):
    """Store job result after processing in both memory and MongoDB"""
    # Store in memory for backward compatibility
    _job_results_store[job_id] = result
    
    # Store in MongoDB for persistence
    try:
        mongodb = await get_mongodb_instance()
        
        # Prepare document for MongoDB
        vulnerability_doc = {
            "job_id": job_id,
            "keyword": result.get("keyword"),
            "status": result.get("status"),
            "timestamp": datetime.utcnow(),
            "processed_at": datetime.fromtimestamp(result.get("timestamp", 0)),
            "total_results": result.get("total_results", 0),
            "vulnerabilities": result.get("vulnerabilities", []),
            "processed_via": result.get("processed_via", "unknown"),
            "error": result.get("error") if result.get("status") == "failed" else None
        }
        
        # Insert into nvd_results collection
        await mongodb.db.nvd_results.insert_one(vulnerability_doc)
        logger.info(f"Stored job result {job_id} in MongoDB NVDReport database")
        
    except Exception as e:
        logger.error(f"Failed to store job result {job_id} in MongoDB: {e}")
        # Continue with in-memory storage even if MongoDB fails

def get_job_result(job_id: str) -> Dict[str, Any]:
    """Retrieve job result"""
    return _job_results_store.get(job_id, {})

async def get_all_job_results_from_mongodb() -> list:
    """Retrieve all vulnerability results from MongoDB"""
    try:
        mongodb = await get_mongodb_instance()
        cursor = mongodb.db.nvd_results.find({}).sort("timestamp", -1)
        results = []
        async for doc in cursor:
            # Convert MongoDB document to dict and handle ObjectId
            doc["_id"] = str(doc["_id"])
            results.append(doc)
        return results
    except Exception as e:
        logger.error(f"Failed to retrieve results from MongoDB: {e}")
        return []

def get_all_job_results() -> Dict[str, Dict[str, Any]]:
    """Retrieve all completed job results"""
    return _job_results_store.copy()

def get_all_completed_jobs() -> Dict[str, Dict[str, Any]]:
    """Get all completed jobs with their results"""
    completed_jobs = {}
    for job_id, result in _job_results_store.items():
        if result.get("status") == "completed":
            completed_jobs[job_id] = result
    return completed_jobs

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
            
            # Use the new get_job_result method
            return await self.get_job_result(job_id)
            
        except Exception as e:
            logger.error(f"Failed to get job metadata for {job_id}: {e}")
            return {}

    async def process_nvd_job_via_kong(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process NVD job by calling Kong Gateway API
        
        Args:
            job_data: Job data containing keyword and metadata
            
        Returns:
            Processing result
        """
        try:
            job_id = job_data.get("job_id")
            keyword = job_data.get("keyword", "vulnerability")
            
            # Kong Gateway URL (adjust as needed)
            kong_url = os.getenv("KONG_URL", "https://kong-b27b67aff4usnspl9.kongcloud.dev")
            nvd_endpoint = f"{kong_url}/nvd/cves/2.0"
            
            # Make request to Kong Gateway
            params = {
                "keywordSearch": keyword,
                "resultsPerPage": 20
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(nvd_endpoint, params=params)
                response.raise_for_status()
                
                nvd_data = response.json()
                
                # Process and store result
                result = {
                    "job_id": job_id,
                    "keyword": keyword,
                    "status": "completed",
                    "timestamp": asyncio.get_event_loop().time(),
                    "total_results": nvd_data.get("totalResults", 0),
                    "vulnerabilities": nvd_data.get("vulnerabilities", []),
                    "processed_via": "kong_gateway"
                }
                
                # Store the result
                if job_id:
                    await store_job_result(job_id, result)
                
                logger.info(f"Job {job_id} processed successfully via Kong: {keyword}")
                return result
                
        except Exception as e:
            error_result = {
                "job_id": job_data.get("job_id"),
                "keyword": job_data.get("keyword", "unknown"),
                "status": "failed",
                "error": str(e),
                "timestamp": asyncio.get_event_loop().time()
            }
            
            # Store the error result
            job_id = job_data.get("job_id")
            if job_id:
                await store_job_result(job_id, error_result)
            
            logger.error(f"Failed to process job {job_data.get('job_id')} via Kong: {e}")
            return error_result

    async def message_callback(self, message: aio_pika.IncomingMessage):
        """
        Callback function to process messages from the queue
        """
        try:
            async with message.process():
                # Parse message body
                job_data = json.loads(message.body.decode())
                
                logger.info(f"Processing job: {job_data.get('job_id')} - {job_data.get('keyword')}")
                
                # Process the job via Kong
                result = await self.process_nvd_job_via_kong(job_data)
                
                logger.info(f"Job completed: {result.get('job_id')} - Status: {result.get('status')}")
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            # Message will be requeued if not acknowledged

    async def start_consumer(self):
        """
        Start consuming messages from the queue and keep running
        """
        try:
            if not self.connection or self.connection.is_closed:
                await self.connect()
            
            if not self.queue:
                raise Exception("Queue not initialized")
            
            # Start consuming with our callback
            await self.queue.consume(self.message_callback)
            
            logger.info(f"Started consuming from queue: {self.queue_name}")
            
            # Keep the consumer running
            try:
                # Wait indefinitely for messages
                await asyncio.Future()  # This will run forever until cancelled
            except asyncio.CancelledError:
                logger.info("Consumer cancelled")
                raise
            
        except Exception as e:
            logger.error(f"Failed to start consumer: {e}")
            raise

    async def get_job_result(self, job_id: str) -> Dict[str, Any]:
        """
        Get the result of a processed job
        
        Args:
            job_id: The job ID to look up
            
        Returns:
            Job result or metadata if still processing
        """
        try:
            # First check if we have a completed result
            result = get_job_result(job_id)
            if result:
                return result
            
            # If no result, check if job exists in metadata (still processing)
            metadata = get_stored_job_metadata(job_id)
            if metadata:
                return {
                    "job_id": job_id,
                    "keyword": metadata.get("keyword", "vulnerability"),
                    "status": "processing",
                    "message": "Job is being processed"
                }
            
            # Job not found
            return {
                "job_id": job_id,
                "status": "not_found",
                "error": "Job not found"
            }
            
        except Exception as e:
            logger.error(f"Failed to get job result for {job_id}: {e}")
            return {
                "job_id": job_id,
                "status": "error",
                "error": str(e)
            }

    async def get_all_job_results(self) -> Dict[str, Any]:
        """
        Get all completed job results
        
        Returns:
            Dictionary with all job results
        """
        try:
            all_results = get_all_completed_jobs()
            return {
                "total_jobs": len(all_results),
                "completed_jobs": len(all_results),
                "jobs": list(all_results.values()),
                "job_ids": list(all_results.keys())
            }
        except Exception as e:
            logger.error(f"Failed to get all job results: {e}")
            return {
                "total_jobs": 0,
                "completed_jobs": 0,
                "jobs": [],
                "job_ids": [],
                "error": str(e)
            }

# Global consumer manager instance
_consumer_manager = None
_consumer_task = None

async def start_queue_consumer():
    """
    Start the RabbitMQ consumer in background
    """
    global _consumer_manager, _consumer_task
    try:
        if _consumer_manager is None:
            _consumer_manager = RabbitMQManager()
            await _consumer_manager.connect()
            
            # Start consuming in background task
            _consumer_task = asyncio.create_task(_consumer_manager.start_consumer())
            
            logger.info("Queue consumer started successfully")
        else:
            logger.info("Consumer already running")
    except Exception as e:
        logger.error(f"Failed to start queue consumer: {e}")

async def stop_queue_consumer():
    """
    Stop the RabbitMQ consumer
    """
    global _consumer_manager, _consumer_task
    try:
        if _consumer_task:
            _consumer_task.cancel()
            try:
                await _consumer_task
            except asyncio.CancelledError:
                pass
            _consumer_task = None
        
        if _consumer_manager:
            await _consumer_manager.close()
            _consumer_manager = None
            logger.info("Queue consumer stopped")
    except Exception as e:
        logger.error(f"Error stopping consumer: {e}")

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
