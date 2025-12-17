import asyncio
import httpx
import time
import sys

BASE_URL = "http://localhost:8002"

async def verify_deployment():
    print(f"Testing NVD Service at {BASE_URL}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Health Check
        try:
            resp = await client.get(f"{BASE_URL}/health")
            print(f"Health Check: {resp.status_code} - {resp.json()}")
        except Exception as e:
            print(f"Health Check Failed: {e}")
            return

        # 2. Submit Job
        keyword = "nginx"
        print(f"\nSubmitting job for keyword: {keyword}")
        try:
            # Endpoint is /api/v1/queue/job
            resp = await client.post(
                f"{BASE_URL}/api/v1/queue/job",
                params={"keyword": keyword}
            )
            
            if resp.status_code != 200:
                print(f"Failed to submit job: {resp.status_code} - {resp.text}")
                return

            data = resp.json()
            job_id = data.get("job_id")
            print(f"Job Submitted! ID: {job_id}, Status: {data.get('status')}")
            
        except Exception as e:
            print(f"Submission Error: {e}")
            return

        # 3. Poll for Results
        print(f"\nPolling for results (Job ID: {job_id})...")
        start_time = time.time()
        while time.time() - start_time < 60: # 60s timeout
            try:
                # Endpoint is /api/v1/results/{job_id}
                resp = await client.get(f"{BASE_URL}/api/v1/results/{job_id}")
                if resp.status_code != 200:
                    print(f"Poll Error: {resp.status_code}")
                    await asyncio.sleep(2)
                    continue
                
                job_data = resp.json()
                status = job_data.get("status")
                print(f"Status: {status}")
                
                if status == "completed":
                    print("\n✅ SUCCESS: Job Completed!")
                    print(f"Total Results: {job_data.get('total_results')}")
                    print(f"Processed Via: {job_data.get('processed_via')}")
                    print(f"Vulnerabilities Found: {len(job_data.get('vulnerabilities', []))}")
                    return
                elif status == "failed":
                    print("\n❌ FAILURE: Job Failed")
                    return
                
                await asyncio.sleep(2)
            except Exception as e:
                print(f"Polling Exception: {e}")
                await asyncio.sleep(2)
        
        print("\n❌ TIMEOUT: Job did not complete in 60s")

if __name__ == "__main__":
    asyncio.run(verify_deployment())
