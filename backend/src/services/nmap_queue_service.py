"""
Nmap Queue Service
"""
import json
import logging
import pika
from config.settings import settings

logger = logging.getLogger(__name__)

class NmapQueueService:
    """Service for managing Nmap scan queue"""
    
    def __init__(self):
        self.host = settings.RABBITMQ_HOST
        self.queue_name = "nmap_scan_queue"
        
    def publish_scan_job(self, job_id: str, target: str) -> bool:
        """Publish a scan job to RabbitMQ"""
        connection = None
        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=self.host)
            )
            channel = connection.channel()
            channel.queue_declare(queue=self.queue_name, durable=True)
            
            message = {
                "job_id": job_id,
                "target": target
            }
            
            channel.basic_publish(
                exchange='',
                routing_key=self.queue_name,
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # make message persistent
                )
            )
            
            logger.info(f"Published Nmap job {job_id} for {target}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish Nmap job: {e}")
            return False
        finally:
            if connection:
                connection.close()
