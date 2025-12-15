"""
Distributed Time Service for synchronized timestamps across microservices
Uses WorldTimeAPI as primary source, falls back to Docker container time
"""
import logging
import httpx
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class TimeService:
    """Service for fetching distributed synchronized time"""
    
    WORLDTIME_API_URL = "http://worldtimeapi.org/api/timezone/Etc/UTC"
    TIMEOUT = 3.0  # seconds
    
    @staticmethod
    async def get_current_timestamp() -> float:
        """
        Get current timestamp from distributed time source.
        Tries WorldTimeAPI first, falls back to Docker time if API fails.
        
        Returns:
            float: Unix timestamp (seconds since epoch)
        """
        # Try WorldTimeAPI first
        try:
            async with httpx.AsyncClient(timeout=TimeService.TIMEOUT) as client:
                response = await client.get(TimeService.WORLDTIME_API_URL)
                if response.status_code == 200:
                    data = response.json()
                    # WorldTimeAPI returns unixtime field
                    timestamp = float(data.get("unixtime", 0))
                    if timestamp > 0:
                        logger.info(f"Time fetched from WorldTimeAPI: {timestamp}")
                        return timestamp
        except Exception as e:
            logger.warning(f"WorldTimeAPI failed: {e}, falling back to Docker time")
        
        # Fallback to Docker container time
        timestamp = datetime.utcnow().timestamp()
        logger.info(f"Using Docker container time: {timestamp}")
        return timestamp
    
    @staticmethod
    async def get_current_datetime() -> datetime:
        """
        Get current datetime from distributed time source.
        
        Returns:
            datetime: Current datetime object
        """
        timestamp = await TimeService.get_current_timestamp()
        return datetime.fromtimestamp(timestamp)
    
    @staticmethod
    async def get_formatted_time(format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
        """
        Get current time formatted as string.
        
        Args:
            format_str: strftime format string
            
        Returns:
            str: Formatted time string
        """
        dt = await TimeService.get_current_datetime()
        return dt.strftime(format_str)
