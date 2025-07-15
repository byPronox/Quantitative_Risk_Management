"""
Logging middleware for request/response tracking
"""
import logging
import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests and responses"""
    
    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.time()
        
        # Log request
        logger.info(
            "Request: %s %s - Client: %s",
            request.method,
            request.url,
            request.client.host if request.client else "unknown"
        )
        
        try:
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log response
            logger.info(
                "Response: %s %s - Status: %d - Time: %.2fs",
                request.method,
                request.url,
                response.status_code,
                process_time
            )
            
            # Add timing header
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                "Error processing %s %s - Time: %.2fs - Error: %s",
                request.method,
                request.url,
                process_time,
                str(e)
            )
            raise
