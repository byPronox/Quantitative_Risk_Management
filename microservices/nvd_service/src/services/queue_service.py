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
from .database_service import DatabaseService
from ..config.settings import settings

logger = logging.getLogger(__name__)

class QueueService:
    """Service for managing RabbitMQ queues for vulnerability analysis."""
    
    def __init__(self, max_retries: int = 5, retry_delay: int = 2):
        self.host = settings.RABBITMQ_HOST
        self.queue_name = settings.RABBITMQ_QUEUE
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
        
        # Database service for automatic persistence (PostgreSQL/Supabase)
        self.database_service = DatabaseService()
        self.nvd_api_service = NVDService() # Initialize NVDService
    
    def _connect(self) -> None:
        """Establece conexión a RabbitMQ con logging robusto."""
        if self.connection and self.connection.is_open and self.channel and self.channel.is_open:
            return

        attempts = 0
        while attempts < self.max_retries:
            try:
                # Close existing closed connection if any
                if self.connection and not self.connection.is_closed:
                    try:
                        self.connection.close()
                    except:
                        pass
                
                self.connection = pika.BlockingConnection(
                    pika.ConnectionParameters(host=self.host)
                )
                self.channel = self.connection.channel()
                self.channel.queue_declare(queue=self.queue_name, durable=True)
                self._connected = True
                logger.info(f"QueueService: Conectado a RabbitMQ en {self.host}, cola: {self.queue_name}")
                return
            except Exception as e:
                attempts += 1
                logger.warning(
                    f"QueueService: Fallo de conexión a RabbitMQ (intento {attempts}/{self.max_retries}): {e}"
                )
                time.sleep(self.retry_delay)
        
        self._connected = False
        logger.error(f"QueueService: No se pudo conectar a RabbitMQ tras {self.max_retries} intentos.")
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
                if (method_frame):
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
            # Log the full traceback for debugging
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            self._job_status[job_id] = "failed"
            self._jobs[job_id]["status"] = "failed"
            # Re-raise to inform the caller
            raise e
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
            # For completed jobs, fetch the result from the in-memory store
            # This is kept for backward compatibility with how results are displayed
            job_data = self._job_results.get(job_id, [])
            result.update({
                "total_results": self._jobs.get(job_id, {}).get("total_results", len(job_data)),
                "vulnerabilities": job_data,
                "processed_via": "queue_consumer"
            })
        return result

    def get_all_job_results(self) -> dict:
        # Return all jobs for /results/all endpoint
        jobs = []
        for job_id, job in self._jobs.items():
            status = self._job_status.get(job_id, "queued")
            job_copy = job.copy()
            job_copy["status"] = status
            if status == "completed":
                job_copy["vulnerabilities"] = self._job_results.get(job_id, [])
                job_copy["total_results"] = job.get("total_results", len(job_copy.get("vulnerabilities", [])))
            jobs.append(job_copy)
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

    def _save_all_existing_jobs_to_mongodb(self):
        """Save all existing completed jobs from /nvd/results/all endpoint to MongoDB Atlas"""
        # This function is deprecated in favor of auto-saving jobs as they are processed.
        # The logic was complex and prone to state issues.
        # Keeping the method signature for now to avoid breaking other parts, but it does nothing.
        logger.info("DEPRECATED: _save_all_existing_jobs_to_mongodb is no longer used.")
        pass

    def start_consumer(self):
        """Inicia el consumer de RabbitMQ y loguea el estado."""
        logger.info("=== START_CONSUMER CALLED ===")
        if self._consumer_thread is not None and self._consumer_thread.is_alive():
            logger.info("Consumer already running, returning...")
            return {"message": "Consumer is already running", "status": "running"}
        
        logger.info("=== INITIATING NEW CONSUMER START ===")
        
        try:
            # Prueba conexión antes de iniciar
            self._connect()
        except Exception as e:
            logger.error(f"QueueService: No se pudo iniciar el consumer por error de conexión: {e}")
            return {"message": "Consumer failed to start", "status": "error", "error": str(e)}
        
        # The complex bulk-save logic is removed. The consumer will now save each job as it completes.
        # This makes the process stateless and more reliable.
        
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
                        # --- FETCH REAL VULNERABILITIES VIA KONG GATEWAY ---
                        vulnerabilities = []
                        total_results = 0
                        try:
                            # Use the NVDService to fetch vulnerabilities, which handles Kong/direct API logic
                            # Since this callback is in a synchronous thread, we need to run the async NVDService call in an event loop.
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            
                            nvd_response = loop.run_until_complete(
                                self.nvd_api_service.search_vulnerabilities(
                                    keywords=keyword,
                                    results_per_page=100 # Use a reasonable default or pass from job metadata
                                )
                            )
                            loop.close()
                            
                            vulnerabilities = nvd_response.get("vulnerabilities", [])
                            total_results = nvd_response.get("total_results", 0)
                            
                            if total_results == 0 or len(vulnerabilities) == 0:
                                logger.warning(f"WARNING: No vulnerabilities found for keyword '{keyword}'")
                                logger.warning(f"Search parameters: keywordSearch={keyword}, resultsPerPage={100}") # Use the actual results_per_page used
                                logger.warning(f"This might indicate the keyword is too specific or no vulnerabilities exist for this term in NVD")
                        except Exception as e:
                            logger.error(f"Error fetching vulnerabilities for '{keyword}': {e}")
                            import traceback
                            logger.error(f"Full error traceback: {traceback.format_exc()}")
                        # --- END FETCH ---
                        
                        # Update in-memory status for short-term checks, but the source of truth is now MongoDB
                        self._job_status[job_id] = "completed"
                        self._jobs[job_id]["status"] = "completed"
                        if job_id in self._processing:
                            self._processing.remove(job_id)
                        self._completed.add(job_id)
                        # We no longer store full results in memory.
                        self._job_results[job_id] = vulnerabilities
                        self._jobs[job_id]["total_results"] = total_results
                        self._jobs[job_id]["vulnerabilities"] = vulnerabilities
                        self._jobs[job_id]["timestamp"] = time.time()
                        self._jobs[job_id]["processed_via"] = "queue_consumer"
                        
                        # --- AUTO-SAVE TO MONGODB ---
                        try:
                            # Clean and transform vulnerabilities data to match MongoDB schema
                            cleaned_vulnerabilities = []
                            for vuln in vulnerabilities:
                                cleaned_vuln = vuln.copy()
                                
                                # Fix CVE tags format if it exists
                                if "cve" in cleaned_vuln and "cveTags" in cleaned_vuln["cve"]:
                                    cve_tags = cleaned_vuln["cve"]["cveTags"]
                                    if isinstance(cve_tags, list):
                                        # Convert list of objects to list of strings
                                        cleaned_tags = []
                                        for tag in cve_tags:
                                            if isinstance(tag, dict):
                                                # Extract tags from the object if it's a dict
                                                if "tags" in tag and isinstance(tag["tags"], list):
                                                    cleaned_tags.extend([str(t) for t in tag["tags"]])
                                                else:
                                                    cleaned_tags.append(str(tag))
                                            else:
                                                cleaned_tags.append(str(tag))
                                        cleaned_vuln["cve"]["cveTags"] = cleaned_tags
                                    elif isinstance(cve_tags, dict):
                                        # If it's a single dict, extract tags
                                        if "tags" in cve_tags and isinstance(cve_tags["tags"], list):
                                            cleaned_vuln["cve"]["cveTags"] = [str(t) for t in cve_tags["tags"]]
                                        else:
                                            cleaned_vuln["cve"]["cveTags"] = [str(cve_tags)]
                                
                                cleaned_vulnerabilities.append(cleaned_vuln)
                            
                            # Create job data in the format expected by MongoDB service
                            job_for_mongodb = {
                                "job_id": job_id,
                                "keyword": keyword,
                                "status": "completed",
                                "total_results": total_results,
                                "timestamp": time.time(),
                                "processed_via": "queue_consumer",
                                "vulnerabilities": cleaned_vulnerabilities
                            }
                            
                            # Save to MongoDB in a background thread to avoid blocking the consumer
                            save_thread = threading.Thread(target=self._save_job_to_mongodb_sync, args=([job_for_mongodb],))
                            save_thread.start()
                            
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
                    if connection:
                        connection.close()
                except:
                    pass
        
        # Start consumer in background thread
        self._consumer_thread = threading.Thread(target=consume, daemon=True)
        self._consumer_thread.start()
        
        return {"message": "Consumer started", "status": "started"}

    def _save_job_to_mongodb_sync(self, jobs_data: List[Dict[str, Any]]):
        """Synchronous helper to save jobs to MongoDB, designed to be run in a thread."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(
                self.database_service.save_job_results(jobs_data) # Pass the job(s) as a list
            )
            loop.close()
            logger.info(f"Successfully saved {len(jobs_data)} job(s) to MongoDB.")
        except Exception as e:
            logger.error(f"Failed to save job to MongoDB in background thread: {e}")

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
