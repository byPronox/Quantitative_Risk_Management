import pika
import os
import ssl
import sys

# Load env vars manually if needed, but we rely on docker env
url = os.getenv('RABBITMQ_URL')
queue = os.getenv('RABBITMQ_QUEUE')

if not url:
    print("Error: RABBITMQ_URL not set")
    sys.exit(1)

print(f"URL: {url}")
print(f"Queue: {queue}")

try:
    params = pika.URLParameters(url)
    if url.startswith('amqps://'):
        context = ssl.create_default_context()
        params.ssl_options = pika.SSLOptions(context, server_hostname=params.host)

    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    channel.queue_declare(queue=queue, durable=True)
    channel.basic_publish(exchange='', routing_key=queue, body='TEST MESSAGE FROM SCRIPT')
    print("Successfully published test message!")
    connection.close()
except Exception as e:
    print(f"Failed to publish: {e}")
    sys.exit(1)
