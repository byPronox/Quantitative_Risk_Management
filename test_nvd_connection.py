import httpx
import asyncio
import os

async def test_nvd():
    api_key = os.getenv("NVD_API_KEY")
    url = "https://services.nvd.nist.gov/rest/json/cves/2.0"
    params = {"resultsPerPage": 1, "keywordSearch": "python"}
    headers = {"apiKey": api_key} if api_key else {}
    
    print(f"Testing connection to: {url}")
    print(f"API Key present: {bool(api_key)}")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers, params=params)
            print(f"Status Code: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"Total Results: {data.get('totalResults')}")
                print("SUCCESS: Connection established and data received.")
            else:
                print(f"FAILURE: {response.text}")
    except Exception as e:
        print(f"EXCEPTION: {e}")

if __name__ == "__main__":
    asyncio.run(test_nvd())
