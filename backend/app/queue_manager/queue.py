# backend/app/queue.py
"""
Simple message queue integration (stub for Azure Service Bus or local alternative).
Replace with Azure Service Bus SDK for production.
"""
import logging
from config.config import settings  # Changed to absolute import

# Use lazy logging formatting for best practices
class MessageQueue:
    def __init__(self):
        # In production, initialize Azure Service Bus or other client here
        self.queue_name = settings.QUEUE_NAME
        logging.info("MessageQueue initialized for queue: %s", self.queue_name)

    def send_message(self, message: dict):
        # In production, send to Azure Service Bus or other MQ
        logging.info("[QUEUE] Message sent to %s: %s", self.queue_name, message)
        # Example: servicebus_client.send_message(...)

# Singleton instance for DI
queue = MessageQueue()
