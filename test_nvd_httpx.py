import httpx
import asyncio
import os

async def test_nvd():
    api_key = os.getenv("NVD_API_KEY")
    url = "https://services.nvd.nist.gov/rest/json/cves/2.0"
    params = {"resultsPerPage": 1, "keywordSearch": "python"}
    
    # Browser User-Agent
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "apiKey": api_key
    } if api_key else {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
    
    print(f"Testing connection to: {url}")
    print(f"API Key present: {bool(api_key)}")
    
    try:
        # Verify=False to rule out cert issues
        async with httpx.AsyncClient(timeout=60.0, verify=False) as client:
            print("Sending request...")
            response = await client.get(url, headers=headers, params=params)
            print(f"Status Code: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"Total Results: {data.get('totalResults')}")
                print("SUCCESS: Connection established and data received.")
            else:
                print(f"FAILURE: {response.text}")
    except httpx.TimeoutException:
        print("TIMEOUT: Request took longer than 60 seconds.")
    except Exception as e:
        print(f"EXCEPTION: {e}")

if __name__ == "__main__":
    asyncio.run(test_nvd())
