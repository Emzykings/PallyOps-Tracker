# ============================================
# PRICEPALLY OPERATIONS TRACKER
# CORS Middleware Configuration
# ============================================

"""
CORS configuration for cross-origin requests.

Allows the frontend (Vercel) to communicate with the backend (Render).
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings


def configure_cors(app: FastAPI) -> None:
    """
    Configure CORS middleware for the application.
    
    Args:
        app: FastAPI application instance
    """
    app.add_middleware(
        CORSMiddleware,
        
        # Origins allowed to make requests
        allow_origins=settings.cors_origins,
        
        # Allow credentials (cookies, authorization headers)
        allow_credentials=True,
        
        # HTTP methods allowed
        allow_methods=[
            "GET",
            "POST",
            "PUT",
            "PATCH",
            "DELETE",
            "OPTIONS",
        ],
        
        # Headers allowed in requests
        allow_headers=[
            "Accept",
            "Accept-Language",
            "Content-Type",
            "Authorization",
            "X-Requested-With",
            "X-Request-ID",
        ],
        
        # Headers exposed to the browser
        expose_headers=[
            "X-Request-ID",
            "X-RateLimit-Limit",
            "X-RateLimit-Remaining",
            "X-RateLimit-Reset",
        ],
        
        # Cache preflight requests for 1 hour
        max_age=3600,
    )


# ============================================
# ADDITIONAL SECURITY HEADERS
# ============================================

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import uuid


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all responses.
    """
    
    async def dispatch(self, request: Request, call_next) -> Response:
        # Generate request ID for tracking
        request_id = str(uuid.uuid4())
        
        # Process request
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Cache control for API responses
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
            response.headers["Pragma"] = "no-cache"
        
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all requests.
    """
    
    async def dispatch(self, request: Request, call_next) -> Response:
        import time
        import logging
        
        logger = logging.getLogger("uvicorn.access")
        
        # Record start time
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Log request details
        logger.info(
            f"{request.method} {request.url.path} "
            f"- Status: {response.status_code} "
            f"- Time: {process_time:.3f}s"
        )
        
        # Add processing time header
        response.headers["X-Process-Time"] = f"{process_time:.3f}"
        
        return response


def configure_security_middleware(app: FastAPI) -> None:
    """
    Configure security middleware.
    
    Args:
        app: FastAPI application instance
    """
    app.add_middleware(SecurityHeadersMiddleware)


def configure_logging_middleware(app: FastAPI) -> None:
    """
    Configure request logging middleware.
    
    Args:
        app: FastAPI application instance
    """
    app.add_middleware(RequestLoggingMiddleware)