import urllib.request
import urllib.error
import os
import ssl
import json

def test_nvd():
    api_key = os.getenv("NVD_API_KEY")
    url = "https://services.nvd.nist.gov/rest/json/cves/2.0?resultsPerPage=1&keywordSearch=python"
    
    print(f"Testing connection to: {url}")
    print(f"API Key present: {bool(api_key)}")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "apiKey": api_key
    } if api_key else {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}

    req = urllib.request.Request(url, headers=headers)
    
    # Create SSL context that ignores errors (just for testing connectivity)
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    try:
        print("Sending request...")
        with urllib.request.urlopen(req, context=ctx, timeout=10) as response:
            print(f"Status Code: {response.getcode()}")
            data = response.read()
            print(f"Data received: {len(data)} bytes")
            try:
                json_data = json.loads(data)
                print(f"Total Results: {json_data.get('totalResults')}")
            except:
                print("Could not parse JSON")
    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code} - {e.reason}")
        print(e.read())
    except urllib.error.URLError as e:
        print(f"URL Error: {e.reason}")
    except Exception as e:
        print(f"General Error: {e}")

if __name__ == "__main__":
    test_nvd()
