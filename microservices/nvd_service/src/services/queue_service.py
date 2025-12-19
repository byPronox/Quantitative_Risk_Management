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
import ssl
from urllib.parse import urlparse
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
        self.rabbitmq_url = settings.RABBITMQ_URL
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
        
        # Parse RABBITMQ_URL to extract connection parameters
        self._connection_params = self._parse_rabbitmq_url()
        
        # Database service for automatic persistence (PostgreSQL/Supabase)
        self.database_service = DatabaseService()
        self.nvd_api_service = NVDService() # Initialize NVDService
    
    def _parse_rabbitmq_url(self) -> pika.ConnectionParameters:
        """Parse RABBITMQ_URL using pika.URLParameters (recommended CloudAMQP method)."""
        try:
            logger.info(f"Original RABBITMQ_URL scheme: {self.rabbitmq_url[:30]}...")
            
            # Use pika.URLParameters for automatic parsing (bulletproof method)
            params = pika.URLParameters(self.rabbitmq_url)
            
            # DEBUG: Log what URLParameters parsed
            logger.info(f"URLParameters parsed - host: {params.host}, port: {params.port}, vhost: {params.virtual_host}")
            logger.info(f"credentials: {params.credentials.__class__.__name__ if params.credentials else 'None'}")
            
            # Force TLS/SSL for AMQPS
            if self.rabbitmq_url.startswith('amqps://'):
                ssl_context = ssl.create_default_context()
                params.ssl_options = pika.SSLOptions(ssl_context, server_hostname=params.host)
                logger.info(f"SSL enabled for AMQPS connection")
            
            # Recommended settings to avoid hangs
            params.heartbeat = 60
            params.blocked_connection_timeout = 300
            params.connection_attempts = 3
            params.retry_delay = 2
            
            logger.info(f"Parsed RabbitMQ connection using URLParameters: host={params.host}:{params.port}, vhost={params.virtual_host}, SSL={params.ssl_options is not None}")
            return params
            
        except Exception as e:
            logger.error(f"Error parsing RABBITMQ_URL with URLParameters: {e}")
            # Fallback to basic connection (should not happen with valid URL)
            return pika.ConnectionParameters(host=self.host)
    
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
                
                self.connection = pika.BlockingConnection(self._connection_params)
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
        connection = None
        try:
            # Create a fresh connection for this operation
            connection = pika.BlockingConnection(self._connection_params)
            channel = connection.channel()
            channel.queue_declare(queue=self.queue_name, durable=True)
            
            message = {
                "keyword": keyword,
                "vulnerabilities": vulnerabilities,
                "timestamp": time.time()
            }
            
            channel.basic_publish(
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
        finally:
            if connection and not connection.is_closed:
                try:
                    connection.close()
                except:
                    pass
    
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
    
    async def add_job(self, keyword: str, metadata: dict) -> str:
        """
        Add a new job to the queue and return the job ID.
        Persists initial 'pending' state to Supabase before publishing to RabbitMQ.
        """
        # Generate Job ID
        job_id = str(int(time.time() * 1000)) + '-' + str(len(self._jobs) + 1)
        
        # Get distributed time
        from ..services.time_service import TimeService
        try:
            created_at = await TimeService.get_current_timestamp()
        except Exception as e:
            logger.warning(f"Failed to get distributed time, using local: {e}")
            created_at = time.time()

        # Create Job Object
        job = {
            "job_id": job_id,
            "keyword": keyword,
            "metadata": metadata,
            "status": "pending",
            "created_at": created_at,
            "processed_via": None,
            "vulnerabilities": [],
            "total_results": 0
        }
        
        # Update in-memory store
        self._jobs[job_id] = job
        self._job_status[job_id] = "pending"
        
        # 1. PERSIST TO SUPABASE (Pending State)
        try:
            # Now we can await directly since we are in an async context
            await self.database_service.save_job_results([job])
            logger.info(f"Job {job_id} persisted to Supabase with status 'pending'")
        except Exception as e:
            logger.error(f"Failed to persist job {job_id} to Supabase: {e}")
            # We might want to raise here to prevent "ghost" jobs in RabbitMQ
            raise e

        # 2. PUBLISH TO RABBITMQ
        connection = None
        try:
            # Create a fresh connection for this operation
            # Note: pika.BlockingConnection is synchronous. 
            # In a high-concurrency async app, we might want to run this in a thread executor,
            # but for now, it's acceptable as it's a quick operation.
            # Alternatively, use aio-pika, but that requires a larger refactor.
            # We'll stick to BlockingConnection but wrap it in to_thread if needed, 
            # but let's keep it simple first as it was working (sync) before.
            connection = pika.BlockingConnection(self._connection_params)
            channel = connection.channel()
            channel.queue_declare(queue=self.queue_name, durable=True)
            
            message = {
                "job_id": job_id,
                "keyword": keyword,
                "metadata": metadata,
                "created_at": created_at
            }
            
            channel.basic_publish(
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
            
            # Update status to failed if RabbitMQ fails
            self._job_status[job_id] = "failed"
            self._jobs[job_id]["status"] = "failed"
            
            # Try to update Supabase to failed
            try:
                job["status"] = "failed"
                await self.database_service.save_job_results([job])
            except:
                pass
                
            # Re-raise to inform the caller
            raise e
        finally:
            if connection and not connection.is_closed:
                try:
                    connection.close()
                except:
                    pass
                    
        return job_id

    def get_job(self, job_id: str) -> dict:
        return self._jobs.get(job_id, {})

    def get_job_result(self, job_id: str) -> dict:
        # Check memory first
        job = self._jobs.get(job_id)
        if job:
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
            
        # Fallback to Database
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            db_job = loop.run_until_complete(self.database_service.get_job(job_id))
            loop.close()
            
            if db_job:
                return {
                    "job_id": db_job.get("job_id"),
                    "keyword": db_job.get("keyword"),
                    "status": db_job.get("status"),
                    "total_results": db_job.get("total_results", 0),
                    "vulnerabilities": db_job.get("vulnerabilities", []),
                    "processed_via": db_job.get("processed_via"),
                    "processed_at": db_job.get("processed_at")
                }
        except Exception as e:
            logger.error(f"Error fetching job {job_id} from database: {e}")
            
        return None

    async def get_all_job_results(self) -> dict:
        """
        Retrieve all jobs from the database (Supabase).
        """
        try:
            # Fetch all jobs from Supabase
            # We need to implement get_all_jobs in database_service first
            jobs = await self.database_service.get_all_jobs()
            
            # Convert to list of dicts if they are objects
            jobs_list = []
            for job in jobs:
                # Ensure job is a dict
                job_dict = dict(job) if not isinstance(job, dict) else job
                jobs_list.append(job_dict)
                
            return {"success": True, "jobs": jobs_list}
        except Exception as e:
            logger.error(f"Error fetching all jobs from database: {e}")
            return {"success": False, "jobs": [], "error": str(e)}

    async def peek_queue_status(self) -> dict:
        # Use a temporary connection/channel to avoid channel closed errors
        queue_size = 0
        try:
            # We need to run the blocking pika call in a thread to avoid blocking the async loop
            def get_rabbitmq_count():
                try:
                    connection = pika.BlockingConnection(self._connection_params)
                    channel = connection.channel()
                    method = channel.queue_declare(queue=self.queue_name, passive=True)
                    count = method.method.message_count
                    connection.close()
                    return count
                except Exception as e:
                    logger.error(f"Failed to get RabbitMQ queue size: {e}")
                    return 0
            
            queue_size = await asyncio.to_thread(get_rabbitmq_count)
            
        except Exception as e:
            logger.error(f"Failed to get queue status wrapper: {e}")

        # Get persistent counts from Database
        db_counts = {
            "pending": 0,
            "processing": 0,
            "completed": 0,
            "failed": 0
        }
        try:
            raw_counts = await self.database_service.get_job_counts()
            # Normalize keys to lowercase to handle potential case differences
            for k, v in raw_counts.items():
                db_counts[k.lower()] = db_counts.get(k.lower(), 0) + v
        except Exception as e:
            logger.error(f"Failed to get DB job counts: {e}")

        return {
            "queue_size": queue_size,
            "jobs": {
                "pending": db_counts.get("pending", 0),
                "processing": db_counts.get("processing", 0),
                "completed": db_counts.get("completed", 0),
                "failed": db_counts.get("failed", 0)
            },
            "queue_name": self.queue_name,
            "status": "healthy"
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
                connection = pika.BlockingConnection(self._connection_params)
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
                        
                        # Ensure job exists in memory (restore from DB if needed or create placeholder)
                        if job_id not in self._jobs:
                            logger.info(f"Job {job_id} not in memory (restart?), initializing placeholder.")
                            self._jobs[job_id] = {
                                "job_id": job_id,
                                "keyword": keyword,
                                "status": "processing",
                                "created_at": time.time(), # Approximate if missing
                                "vulnerabilities": [],
                                "total_results": 0
                            }
                            self._job_status[job_id] = "processing"
                            self._processing.add(job_id)
                        else:
                            self._job_status[job_id] = "processing"
                            self._jobs[job_id]["status"] = "processing"
                            self._processing.add(job_id)
                        
                        # --- UPDATE SUPABASE TO PROCESSING ---
                        try:
                            # Get distributed time
                            from ..services.time_service import TimeService
                            try:
                                processed_at = asyncio.run(TimeService.get_current_timestamp())
                            except Exception as time_err:
                                logger.warning(f"Failed to get distributed time, using local: {time_err}")
                                processed_at = time.time()
                                
                            # Create update object
                            job_update = {
                                "job_id": job_id,
                                "status": "processing",
                                "processed_at": processed_at,
                                "processed_via": "queue_consumer" # Initial marker
                            }
                            
                            # Save to Supabase synchronously using a local DatabaseService instance
                            # This avoids sharing the asyncpg pool across threads/loops
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            
                            db_service = DatabaseService()
                            try:
                                loop.run_until_complete(db_service.save_job_results([job_update]))
                            finally:
                                loop.run_until_complete(db_service.disconnect())
                                loop.close()
                                
                            logger.info(f"Job {job_id} status updated to 'processing' in Supabase")
                        except Exception as e:
                            logger.error(f"Failed to update job {job_id} status to processing: {e}")
                        # --- END UPDATE ---
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
                        
                        # Update in-memory status for short-term checks
                        self._job_status[job_id] = "completed"
                        self._jobs[job_id]["status"] = "completed"
                        if job_id in self._processing:
                            self._processing.remove(job_id)
                        self._completed.add(job_id)
                        self._job_results[job_id] = vulnerabilities
                        self._jobs[job_id]["total_results"] = total_results
                        self._jobs[job_id]["vulnerabilities"] = vulnerabilities
                        
                        # Use distributed time service for synchronized timestamps
                        from ..services.time_service import TimeService
                        try:
                            # Get distributed timestamp
                            distributed_timestamp = asyncio.run(TimeService.get_current_timestamp())
                            logger.info(f"Using distributed timestamp: {distributed_timestamp}")
                        except Exception as time_err:
                            logger.warning(f"Failed to get distributed time, using local: {time_err}")
                            distributed_timestamp = time.time()
                        
                        self._jobs[job_id]["timestamp"] = distributed_timestamp
                        self._jobs[job_id]["processed_at"] = distributed_timestamp
                        self._jobs[job_id]["processed_via"] = "queue_consumer"
                        
                        # --- AUTO-SAVE TO SUPABASE DATABASE ---
                        try:
                            # Clean and transform vulnerabilities data to match database schema
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
                            
                            # Create job data for Supabase
                            job_for_database = {
                                "job_id": job_id,
                                "keyword": keyword,
                                "status": "completed",
                                "total_results": total_results,
                                "timestamp": distributed_timestamp,
                                "processed_at": distributed_timestamp,
                                "processed_via": "queue_consumer",
                                "vulnerabilities": cleaned_vulnerabilities,
                                "vulnerabilities_count": len(cleaned_vulnerabilities)
                            }
                            
                            # Save to Supabase in a background thread to avoid blocking the consumer
                            save_thread = threading.Thread(target=self._save_job_to_database_sync, args=([job_for_database],))
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

    def _save_job_to_database_sync(self, jobs_data: List[Dict[str, Any]]):
        """Synchronous helper to save jobs to Supabase, designed to be run in a thread."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            db_service = DatabaseService()
            try:
                loop.run_until_complete(
                    db_service.save_job_results(jobs_data) # Pass the job(s) as a list
                )
            finally:
                loop.run_until_complete(db_service.disconnect())
                loop.close()
                
            logger.info(f"Successfully saved {len(jobs_data)} job(s) to Supabase.")
        except Exception as e:
            logger.error(f"Failed to save job to Supabase in background thread: {e}")

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
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get queue metrics."""
        try:
            status = await self.peek_queue_status()
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
