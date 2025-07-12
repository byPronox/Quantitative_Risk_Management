"""
Queue Management Service for handling vulnerability analysis queues.
"""
import pika
import json
import logging
import os
import time
from typing import List, Dict, Any, Optional

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
    
    def peek_queue_status(self) -> Dict[str, Any]:
        """
        Get queue status without consuming messages.
        
        Returns:
            Queue status information
        """
        try:
            self._connect()
            
            # Get queue info
            method = self.channel.queue_declare(queue=self.queue_name, passive=True)
            message_count = method.method.message_count
            
            # Peek at messages without consuming them
            messages = []
            temp_messages = []
            
            # Get messages temporarily
            while True:
                method_frame, properties, body = self.channel.basic_get(self.queue_name)
                if method_frame:
                    message = json.loads(body)
                    messages.append(message)
                    temp_messages.append((method_frame, properties, body))
                else:
                    break
            
            # Put messages back
            for method_frame, properties, body in temp_messages:
                self.channel.basic_publish(
                    exchange='',
                    routing_key=self.queue_name,
                    body=body,
                    properties=properties
                )
                self.channel.basic_ack(method_frame.delivery_tag)
            
            keywords = [msg.get("keyword", "unknown") for msg in messages]
            total_vulnerabilities = sum(len(msg.get("vulnerabilities", [])) for msg in messages)
            
            return {
                "queue_size": len(messages),
                "keywords": keywords,
                "total_vulnerabilities": total_vulnerabilities,
                "queue_name": self.queue_name
            }
            
        except Exception as e:
            logger.error("Failed to get queue status: %s", e)
            return {
                "queue_size": 0,
                "keywords": [],
                "total_vulnerabilities": 0,
                "error": str(e)
            }
    
    def clear_queue(self) -> Dict[str, Any]:
        """
        Clear all messages from the queue.
        
        Returns:
            Information about cleared items
        """
        try:
            self._connect()
            
            # Count messages before clearing
            messages = self.get_all_vulnerability_data()
            cleared_count = len(messages)
            
            logger.info("Cleared %d messages from queue", cleared_count)
            
            return {
                "message": "Queue cleared successfully",
                "cleared_items": cleared_count,
                "queue_name": self.queue_name
            }
            
        except Exception as e:
            logger.error("Failed to clear queue: %s", e)
            return {
                "message": "Failed to clear queue",
                "error": str(e),
                "cleared_items": 0
            }
    
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
