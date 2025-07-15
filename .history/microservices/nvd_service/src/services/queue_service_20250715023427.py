"""
Queue Management Service for handling vulnerability analysis queues.
"""
import pika
import json
import logging
import os
import time
import threading
import asyncio
import httpx
from typing import List, Dict, Any, Optional
from .nvd_service import NVDService
from .mongodb_service import MongoDBService

logger = logging.getLogger(__name__)

class QueueService:
    """Service for managing RabbitMQ queues for vulnerability analysis."""
    
    def __init__(self, max_retries: int = 5, retry_delay: int = 2):
        self.host = os.getenv("RABBITMQ_HOST", "rabbitmq")
        self.queue_name = os.getenv("RABBITMQ_QUEUE", "nvd_searches")
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.connection = None
        self.channel = None
        self._connected = False
        self._jobs = {}  # In-memory job store
        self._job_status = {}  # Track job status: queued, processing, completed
        self._job_results = {}  # Store results for completed jobs
        self._pending_queue = []  # Simulate RabbitMQ pending jobs
        self._processing = set()  # Simulate jobs being processed
        self._completed = set()   # Simulate completed jobs
        self._consumer_thread = None  # Track consumer thread
        
        # MongoDB service for automatic persistence
        self.mongodb_service = MongoDBService()
    
    def _connect(self) -> None:
        """Establish connection to RabbitMQ with retry logic."""
        if self._connected:
            return
        
        attempts = 0
        while attempts < self.max_retries:
            try:
                self.connection = pika.BlockingConnection(
                    pika.ConnectionParameters(host=self.host)
                )
                self.channel = self.connection.channel()
                self.channel.queue_declare(queue=self.queue_name, durable=True)
                self._connected = True
                logger.info("Queue service connected to queue: %s (RabbitMQ)", self.queue_name)
                return
            except Exception as e:
                attempts += 1
                logger.warning(
                    "RabbitMQ connection failed (attempt %d/%d): %s", 
                    attempts, self.max_retries, e
                )
                time.sleep(self.retry_delay)
        
        raise ConnectionError(f"Could not connect to RabbitMQ after {self.max_retries} attempts.")
    
    def disconnect(self) -> None:
        """Close RabbitMQ connection."""
        try:
            if self.connection and not self.connection.is_closed:
                self.connection.close()
                self._connected = False
                logger.info("Queue service disconnected from RabbitMQ")
        except Exception as e:
            logger.error("Error disconnecting from RabbitMQ: %s", e)
    
    def add_vulnerability_data(self, keyword: str, vulnerabilities: List[Dict[str, Any]]) -> bool:
        """
        Add vulnerability data to the analysis queue.
        
        Args:
            keyword: Search keyword
            vulnerabilities: List of vulnerability data
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self._connect()
            
            message = {
                "keyword": keyword,
                "vulnerabilities": vulnerabilities,
                "timestamp": time.time()
            }
            
            self.channel.basic_publish(
                exchange='',
                routing_key=self.queue_name,
                body=json.dumps(message),
                properties=pika.BasicProperties(delivery_mode=2)  # Persistent message
            )
            
            logger.info(
                "Added vulnerability data to queue: keyword='%s', count=%d", 
                keyword, len(vulnerabilities)
            )
            return True
            
        except Exception as e:
            logger.error("Failed to add vulnerability data to queue: %s", e)
            return False
    
    def get_all_vulnerability_data(self) -> List[Dict[str, Any]]:
        """
        Retrieve all vulnerability data from the queue.
        
        Returns:
            List of vulnerability data messages
        """
        try:
            self._connect()
            messages = []
            
            while True:
                method_frame, _, body = self.channel.basic_get(self.queue_name)
                if method_frame:
                    message = json.loads(body)
                    messages.append(message)
                    self.channel.basic_ack(method_frame.delivery_tag)
                else:
                    break
            
            logger.info("Retrieved %d messages from queue", len(messages))
            return messages
            
        except Exception as e:
            logger.error("Failed to retrieve vulnerability data from queue: %s", e)
            return []
    
    def add_job(self, keyword: str, metadata: dict) -> str:
        """
        Add a new job to the queue and return the job ID.
        Now publishes the job to RabbitMQ instead of just storing in memory.
        """
        job_id = str(int(time.time() * 1000)) + '-' + str(len(self._jobs) + 1)
        job = {
            "job_id": job_id,
            "keyword": keyword,
            "metadata": metadata,
            "status": "queued",
            "created_at": time.time(),
        }
        self._jobs[job_id] = job
        self._job_status[job_id] = "queued"
        # Publish job to RabbitMQ
        try:
            self._connect()
            message = {
                "job_id": job_id,
                "keyword": keyword,
                "metadata": metadata,
                "created_at": job["created_at"]
            }
            self.channel.basic_publish(
                exchange='',
                routing_key=self.queue_name,
                body=json.dumps(message),
                properties=pika.BasicProperties(delivery_mode=2)  # Persistent message
            )
            logger.info(f"Job published to RabbitMQ: {job_id} for keyword: {keyword}")
        except Exception as e:
            logger.error(f"Failed to publish job to RabbitMQ: {e}")
            self._job_status[job_id] = "failed"
            self._jobs[job_id]["status"] = "failed"
        return job_id

    def get_job(self, job_id: str) -> dict:
        return self._jobs.get(job_id, {})

    def get_job_result(self, job_id: str) -> dict:
        # Return job info with status
        job = self._jobs.get(job_id)
        if not job:
            return None
        status = self._job_status.get(job_id, "queued")
        result = {
            "job_id": job_id,
            "keyword": job.get("keyword"),
            "status": status,
        }
        if status == "completed":
            result.update({
                "total_results": len(self._job_results.get(job_id, [])),
                "vulnerabilities": self._job_results.get(job_id, []),
                "processed_via": "queue_consumer"
            })
        return result

    def get_all_job_results(self) -> dict:
        """Return all jobs for /results/all endpoint, combining in-memory and MongoDB data"""
        jobs = []
        
        # Add in-memory jobs first
        for job_id, job in self._jobs.items():
            status = self._job_status.get(job_id, "queued")
            job_copy = job.copy()
            job_copy["status"] = status
            if status == "completed":
                job_copy["vulnerabilities"] = self._job_results.get(job_id, [])
                job_copy["total_results"] = len(self._job_results.get(job_id, []))
            jobs.append(job_copy)
        
        # Also include jobs from MongoDB Atlas
        try:
            import asyncio
            logger.info("Attempting to fetch MongoDB jobs...")
            
            # Create new event loop for this thread
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            # Connect to MongoDB if not already connected
            loop.run_until_complete(self.mongodb_service.connect())
            
            # Get jobs from MongoDB
            mongodb_jobs = loop.run_until_complete(self.mongodb_service.get_all_jobs())
            logger.info(f"Retrieved {len(mongodb_jobs)} jobs from MongoDB Atlas")
            
            # Add MongoDB jobs that aren't already in memory
            existing_job_ids = {job["job_id"] for job in jobs}
            mongodb_count = 0
            for mongo_job in mongodb_jobs:
                if mongo_job.get("job_id") not in existing_job_ids:
                    # Convert MongoDB format to the expected format
                    formatted_job = {
                        "job_id": mongo_job.get("job_id"),
                        "keyword": mongo_job.get("keyword"),
                        "status": mongo_job.get("status", "completed"),
                        "total_results": mongo_job.get("total_results", 0),
                        "vulnerabilities": mongo_job.get("vulnerabilities", []),
                        "processed_via": mongo_job.get("processed_via", "mongodb"),
                        "created_at": mongo_job.get("processed_at", mongo_job.get("timestamp", time.time())),
                        "timestamp": mongo_job.get("processed_at", mongo_job.get("timestamp", time.time()))
                    }
                    jobs.append(formatted_job)
                    mongodb_count += 1
            
            logger.info(f"Retrieved {len(jobs)} total jobs ({len(self._jobs)} in-memory + {mongodb_count} from MongoDB)")
            
        except Exception as e:
            logger.error(f"Failed to get MongoDB jobs: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
        
        return {"jobs": jobs}

    def peek_queue_status(self) -> dict:
        # Use a temporary connection/channel to avoid channel closed errors
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.host))
            channel = connection.channel()
            method = channel.queue_declare(queue=self.queue_name, passive=True)
            pending = method.method.message_count
            connection.close()
            processing = len(self._processing)
            completed = len(self._completed)
            return {
                "queue_size": pending,
                "pending": pending,
                "processing": processing,
                "completed": completed,
                "queue_name": self.queue_name,
                "status": "healthy"
            }
        except Exception as e:
            logger.error(f"Failed to get queue status: {e}")
            return {
                "queue_size": 0,
                "pending": 0,
                "processing": 0,
                "completed": 0,
                "queue_name": self.queue_name,
                "status": "unhealthy",
                "error": str(e)
            }

    def start_consumer(self):
        """Start a persistent RabbitMQ consumer in a background thread"""
        if self._consumer_thread is not None and self._consumer_thread.is_alive():
            return {"message": "Consumer is already running", "status": "running"}
        
        # Start a real RabbitMQ consumer in a background thread, with its own connection/channel
        def consume():
            connection = None
            try:
                connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.host))
                channel = connection.channel()
                channel.queue_declare(queue=self.queue_name, durable=True)
                
                # Set up callback for processing messages
                def callback(ch, method, properties, body):
                    try:
                        job_data = json.loads(body)
                        job_id = job_data.get("job_id")
                        keyword = job_data.get("keyword")
                        if not job_id or not keyword:
                            logger.warning("Received job without job_id or keyword, skipping")
                            ch.basic_ack(method.delivery_tag)
                            return
                            
                        logger.info(f"Processing job: {job_id} for keyword: {keyword}")
                        self._job_status[job_id] = "processing"
                        self._jobs[job_id]["status"] = "processing"
                        self._processing.add(job_id)
                        # --- FETCH REAL VULNERABILITIES VIA BACKEND/KONG ---
                        vulnerabilities = []
                        total_results = 0
                        try:
                            backend_url = os.getenv("BACKEND_URL", "http://backend:8000")
                            # Llama al endpoint del backend que pasa por Kong
                            with httpx.Client(timeout=60.0) as client:
                                response = client.get(f"{backend_url}/nvd", params={"keyword": keyword})
                                if response.status_code == 200:
                                    data = response.json()
                                    vulnerabilities = data.get("vulnerabilities", [])
                                    total_results = data.get("totalResults", 0)
                                else:
                                    logger.error(f"Failed to fetch vulnerabilities for {keyword}: {response.status_code} - {response.text}")
                        except Exception as e:
                            logger.error(f"Error fetching vulnerabilities for {keyword}: {e}")
                        # --- END FETCH ---
                        
                        self._job_status[job_id] = "completed"
                        self._jobs[job_id]["status"] = "completed"
                        self._processing.remove(job_id)
                        self._completed.add(job_id)
                        self._job_results[job_id] = vulnerabilities
                        self._jobs[job_id]["total_results"] = total_results
                        self._jobs[job_id]["vulnerabilities"] = vulnerabilities
                        self._jobs[job_id]["timestamp"] = time.time()
                        self._jobs[job_id]["processed_via"] = "queue_consumer"
                        
                        # --- AUTO-SAVE TO MONGODB ---
                        try:
                            # Create job data in the format expected by MongoDB service
                            job_for_mongodb = {
                                "job_id": job_id,
                                "keyword": keyword,
                                "status": "completed",
                                "total_results": total_results,
                                "timestamp": time.time(),
                                "processed_via": "queue_consumer",
                                "vulnerabilities": vulnerabilities
                            }
                            
                            # Save to MongoDB asynchronously in a new thread
                            def save_to_mongodb():
                                try:
                                    import asyncio
                                    loop = asyncio.new_event_loop()
                                    asyncio.set_event_loop(loop)
                                    loop.run_until_complete(
                                        self.mongodb_service.save_job_results([job_for_mongodb])
                                    )
                                    loop.close()
                                    logger.info(f"Job {job_id} automatically saved to MongoDB")
                                except Exception as mongo_error:
                                    logger.error(f"Failed to auto-save job {job_id} to MongoDB: {mongo_error}")
                            
                            # Save in background thread to not block queue processing
                            mongodb_thread = threading.Thread(target=save_to_mongodb, daemon=True)
                            mongodb_thread.start()
                            
                        except Exception as auto_save_error:
                            logger.error(f"Error setting up auto-save to MongoDB for job {job_id}: {auto_save_error}")
                        # --- END AUTO-SAVE ---
                        
                        logger.info(f"Job processed and completed: {job_id} (found {len(vulnerabilities)} vulns)")
                        ch.basic_ack(method.delivery_tag)
                    except Exception as e:
                        logger.error(f"Error processing job from queue: {e}")
                        ch.basic_nack(method.delivery_tag, requeue=False)
                
                # Start consuming messages
                channel.basic_consume(queue=self.queue_name, on_message_callback=callback)
                logger.info("Consumer started, waiting for messages...")
                channel.start_consuming()
                
            except Exception as e:
                logger.error(f"Consumer error: {e}")
            finally:
                try:
                    if 'connection' in locals():
                        connection.close()
                except:
                    pass
        
        # Start consumer in background thread
        self._consumer_thread = threading.Thread(target=consume, daemon=True)
        self._consumer_thread.start()
        
        return {"message": "Consumer started", "status": "started"}

    def stop_consumer(self):
        # No-op for simulation
        return {"message": "Consumer stopped"}
    
    def health_check(self) -> bool:
        """Check if the queue service is healthy."""
        try:
            self._connect()
            return self._connected
        except Exception as e:
            logger.error("Queue health check failed: %s", e)
            return False
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get queue metrics."""
        try:
            status = self.peek_queue_status()
            return {
                "uptime_seconds": 0,  # Would need to track service start time
                "total_requests": 0,  # Would need to track this
                "successful_requests": 0,  # Would need to track this
                "failed_requests": 0,  # Would need to track this
                "average_response_time": 0.0,  # Would need to track this
                "queue_size": status.get("queue_size", 0),
                "active_jobs": 0,  # Would need job tracking
            }
        except Exception as e:
            logger.error("Failed to get metrics: %s", e)
            return {
                "uptime_seconds": 0,
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "average_response_time": 0.0,
                "queue_size": 0,
                "active_jobs": 0,
            }
    
    def __enter__(self):
        """Context manager entry."""
        self._connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
