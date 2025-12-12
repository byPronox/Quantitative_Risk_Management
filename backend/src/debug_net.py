import socket
import sys

host = "aws-0-us-east-1.pooler.supabase.com"
port = 6543

print(f"Testing TCP connection to {host}:{port}...")

try:
    s = socket.create_connection((host, port), timeout=5)
    print("SUCCESS! TCP connection established.")
    s.close()
except Exception as e:
    print(f"FAILED: {e}")
