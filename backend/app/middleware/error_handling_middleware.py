# backend/app/middleware/error_handling_middleware.py
"""
Error handling middleware for consistent error responses.
"""
import logging
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("backend_middleware")

class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except HTTPException as exc:
            # Re-raise HTTP exceptions to be handled by FastAPI
            raise exc
        except Exception as exc:
            # Log the error
            logger.error(f"Unhandled error in {request.method} {request.url}: {str(exc)}")
            
            # Return a generic error response
            return JSONResponse(
                status_code=500,
                content={"error": "Internal server error", "detail": str(exc)}
            )
