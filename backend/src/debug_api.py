import requests
import sys

# Credentials provided by user
SUPABASE_URL = "https://cjkgiqsfqykxrpnauslk.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNqa2dpcXNmcXlreHJwbmF5c2xrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjU0NjMwMzAsImV4cCI6MjA4MTAzOTAzMH0.-MitwDMjoIz6twEXE2cgsEW8dWafllQZCWGwWjDWAI0"

print(f"Testing REST API connection to {SUPABASE_URL}...")

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}"
}

try:
    # Try to fetch the root or a simple endpoint
    # Usually /rest/v1/ is the entry point
    response = requests.get(f"{SUPABASE_URL}/rest/v1/", headers=headers, timeout=10)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text[:200]}...")
    
    if response.status_code == 200:
        print("SUCCESS! Connected to Supabase REST API.")
    else:
        print("Connected, but received non-200 status (this is good, it means network works).")
        
except Exception as e:
    print(f"FAILED: {e}")
