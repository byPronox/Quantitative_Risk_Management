import os
import json
from pathlib import Path

# Always load secrets from /app/.env.json in Docker
ENV_PATH = Path("/app/.env.json")
if ENV_PATH.exists():
    with open(ENV_PATH, "r", encoding="utf-8") as f:
        secrets = json.load(f)
else:
    secrets = {}

def get_secret(key, default=None):
    return secrets.get(key) or os.getenv(key, default)
