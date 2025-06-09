# backend/app/queue.py
"""
Simple message queue integration (RabbitMQ implementation).
"""
import logging
import pika
import json
import os
import time

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_QUEUE = os.getenv("RABBITMQ_QUEUE", "nvd_searches")

# Use lazy logging formatting for best practices
class MessageQueue:
    def __init__(self, max_retries=5, retry_delay=2):
        self.connection = None
        self.channel = None
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._connected = False
        # Do not connect at init time

    def _connect(self):
        if self._connected:
            return
        attempts = 0
        while attempts < self.max_retries:
            try:
                self.connection = pika.BlockingConnection(pika.ConnectionParameters(
                    host=RABBITMQ_HOST
                ))
                self.channel = self.connection.channel()
                self.channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)
                self._connected = True
                logging.info("MessageQueue connected to queue: %s (RabbitMQ)", RABBITMQ_QUEUE)
                return
            except Exception as e:
                attempts += 1
                logging.warning("RabbitMQ connection failed (attempt %d/%d): %s", attempts, self.max_retries, e)
                time.sleep(self.retry_delay)
        raise ConnectionError(f"Could not connect to RabbitMQ after {self.max_retries} attempts.")

    def send_message(self, message: dict):
        try:
            self._connect()
            self.channel.basic_publish(
                exchange='',
                routing_key=RABBITMQ_QUEUE,
                body=json.dumps(message),
                properties=pika.BasicProperties(delivery_mode=2)  # make message persistent
            )
            logging.info("[QUEUE] Message sent to %s: %s", RABBITMQ_QUEUE, message)
        except Exception as e:
            logging.error("Failed to send message to RabbitMQ: %s", e)
            raise

    def get_all_messages(self):
        try:
            self._connect()
            messages = []
            while True:
                method_frame, _, body = self.channel.basic_get(RABBITMQ_QUEUE)
                if method_frame:
                    messages.append(json.loads(body))
                    self.channel.basic_ack(method_frame.delivery_tag)
                else:
                    break
            return messages
        except Exception as e:
            logging.error("Failed to get messages from RabbitMQ: %s", e)
            raise
