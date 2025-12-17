import asyncio
import logging
import sys
import os
from unittest.mock import MagicMock, patch

# Add microservices/nvd_service to path so we can import src as a package
sys.path.append(os.path.join(os.getcwd(), "microservices", "nvd_service"))

# Load .env from root
env_path = os.path.join(os.getcwd(), ".env")
if os.path.exists(env_path):
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                if key and value:
                    os.environ[key] = value

from src.services.queue_service import QueueService
from src.services.database_service import DatabaseService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_async_flow():
    logger.info("Starting NVD Async Flow Test")
    
    # Mock RabbitMQ to avoid connection errors
    with patch('pika.BlockingConnection') as mock_connection:
        # Setup mock
        mock_channel = MagicMock()
        mock_connection.return_value.channel.return_value = mock_channel
        
        # Initialize Service
        queue_service = QueueService()
        database_service = DatabaseService()
        
        # 1. Test Producer (add_job)
        logger.info("Testing Producer (add_job)...")
        # Run in thread to simulate FastAPI thread pool and allow new_event_loop() to work
        job_id = await asyncio.to_thread(queue_service.add_job, "test_keyword", {"test": "metadata"})
        logger.info(f"Job added with ID: {job_id}")
        
        # Wait for persistence
        await asyncio.sleep(2)
        
        # Verify in Supabase
        logger.info(f"Verifying 'pending' status in Supabase for job {job_id}...")
        job = await database_service.get_job(job_id)
        
        if job and job['status'] == 'pending':
            logger.info("✅ SUCCESS: Job found in Supabase with status 'pending'")
        else:
            logger.error(f"❌ FAILURE: Job not found or status incorrect. Job: {job}")
            # Debug: List all jobs
            all_jobs = await database_service.get_all_jobs()
            logger.info(f"All jobs in DB: {[j.get('job_id') for j in all_jobs]}")
            raise Exception("Job not found or status incorrect")

        # 2. Simulate Consumer Processing (Update to Processing)
        logger.info("Simulating Consumer (Update to 'processing')...")
        
        # Manually update to processing (mimicking what consumer does)
        job_update = {
            "job_id": job_id,
            "status": "processing",
            "processed_at": 1234567890.0, # Mock timestamp
            "processed_via": "test_script"
        }
        await database_service.save_job_results([job_update])
        
        # Verify in Supabase
        job = await database_service.get_job(job_id)
        if job and job['status'] == 'processing':
            logger.info("✅ SUCCESS: Job updated to 'processing' in Supabase")
        else:
            logger.error(f"❌ FAILURE: Job status not updated. Job: {job}")
            raise Exception("Job status not updated")

        logger.info("Test Completed Successfully")

if __name__ == "__main__":
    asyncio.run(test_async_flow())
