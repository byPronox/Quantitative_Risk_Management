"""
Time Service for synchronizing system time
"""
import logging
import httpx
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

class TimeService:
    """
    Service to provide a single source of truth for time across the system.
    Tries to fetch from an external API first, falls back to system time.
    """
    
    def __init__(self):
        self.time_api_url = "http://worldtimeapi.org/api/timezone/Etc/UTC"
        self.timeout = 5.0  # seconds

    async def get_current_time(self) -> datetime:
        """
        Get the current time from the external API or fallback to system time.
        Returns a UTC datetime object.
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(self.time_api_url)
                
                if response.status_code == 200:
                    data = response.json()
                    # Parse the datetime string (e.g., "2023-10-27T10:00:00.123456+00:00")
                    # We use fromisoformat which handles the offset
                    external_time = datetime.fromisoformat(data["datetime"])
                    logger.info(f"Fetched time from external API: {external_time}")
                    return external_time
                else:
                    logger.warning(f"Time API returned status {response.status_code}. Falling back to system time.")
                    
        except httpx.RequestError as e:
            logger.warning(f"Failed to connect to Time API: {e}. Falling back to system time.")
        except Exception as e:
            logger.error(f"Unexpected error in TimeService: {e}. Falling back to system time.")
            
        # Fallback
        system_time = datetime.utcnow()
        logger.info(f"Using system time (fallback): {system_time}")
        return system_time
