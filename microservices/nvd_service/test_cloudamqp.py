#!/usr/bin/env python3
"""Test CloudAMQP connection directly"""
import os
import ssl
import pika

url = os.environ.get("RABBITMQ_URL", "NOT_SET")
print(f"RABBITMQ_URL: {url[:60]}...")

params = pika.URLParameters(url)

# Forzar TLS (AMQPS)
ctx = ssl.create_default_context()
params.ssl_options = pika.SSLOptions(ctx, server_hostname=params.host)

# Recomendado para evitar cuel gues
params.heartbeat = 60
params.blocked_connection_timeout = 300
params.connection_attempts = 3
params.retry_delay = 2

print(f"Connecting to host={params.host}:{params.port}, vhost={params.virtual_host}")

try:
    conn = pika.BlockingConnection(params)
    ch = conn.channel()

    # Prueba rápida
    ch.queue_declare(queue="test_queue", durable=True)
    ch.basic_publish(
        exchange="",
        routing_key="test_queue",
        body=b"hello",
        properties=pika.BasicProperties(delivery_mode=2),
    )

    print("✅ OK: conectado y publish listo")
    conn.close()
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
