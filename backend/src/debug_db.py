import os
import sys
import urllib.parse
from sqlalchemy import create_engine, text

password = "justingomezcoello123"
encoded_password = urllib.parse.quote_plus(password)

host = "aws-0-us-east-1.pooler.supabase.com"
dbname = "postgres"
project_ref = "cjkgiqsfqykxrpnauslk"

configs = [
    {"port": "6543", "user": f"postgres.{project_ref}", "desc": "User with Suffix (6543)"},
    {"port": "5432", "user": f"postgres.{project_ref}", "desc": "User with Suffix (5432)"},
    {"port": "6543", "user": "postgres", "desc": "User NO Suffix (6543)"},
    {"port": "5432", "user": "postgres", "desc": "User NO Suffix (5432)"},
]

print(f"Testing connectivity to {host} with password '{password}'...")

for config in configs:
    user = config["user"]
    port = config["port"]
    desc = config["desc"]
    
    db_url = f"postgresql://{user}:{encoded_password}@{host}:{port}/{dbname}"
    safe_url = f"postgresql://{user}:****@{host}:{port}/{dbname}"
    
    print(f"\n--- Testing {desc} ---")
    print(f"URL: {safe_url}")
    
    try:
        engine = create_engine(db_url, connect_args={'connect_timeout': 5})
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            print("SUCCESS! Connection established.")
            print(f"Result: {result.fetchone()}")
            break
    except Exception as e:
        print(f"FAILED: {e}")
