# ============================================
# PRICEPALLY OPERATIONS TRACKER
# Main Application Entry Point
# ============================================

"""
FastAPI application entry point.

This file:
- Creates the FastAPI application instance
- Configures middleware (CORS, security, logging)
- Registers all routers
- Sets up error handlers
- Configures startup/shutdown events
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import init_db, check_db_connection
from app.routers import api_router
from app.routers.health import router as health_router
from app.middleware.cors_middleware import (
    configure_cors,
    configure_security_middleware,
    configure_logging_middleware,
)
from app.middleware.error_handlers import (
    register_error_handlers,
    register_custom_exception_handlers,
)
from app.utils.timezone import get_current_time


# ============================================
# LOGGING CONFIGURATION
# ============================================

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger = logging.getLogger(__name__)


# ============================================
# LIFESPAN CONTEXT MANAGER
# ============================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Handles startup and shutdown events.
    """
    # -------- STARTUP --------
    logger.info("=" * 50)
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info("=" * 50)
    
    # Check database connection
    logger.info("Checking database connection...")
    if check_db_connection():
        logger.info("✅ Database connection successful")
    else:
        logger.error("❌ Database connection failed!")
        # Continue anyway - the app might recover
    
    # Initialize database tables
    logger.info("Initializing database tables...")
    try:
        init_db()
        logger.info("✅ Database tables initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {e}")
    
    logger.info(f"🌍 Timezone: {settings.timezone}")
    logger.info(f"🔧 Debug mode: {settings.debug}")
    logger.info(f"🚀 Server ready at http://{settings.host}:{settings.port}")
    logger.info("=" * 50)
    
    yield  # Application runs here
    
    # -------- SHUTDOWN --------
    logger.info("=" * 50)
    logger.info("Shutting down application...")
    logger.info("👋 Goodbye!")
    logger.info("=" * 50)


# ============================================
# CREATE FASTAPI APPLICATION
# ============================================

app = FastAPI(
    title=settings.app_name,
    description="""
## Pricepally Operations Time Efficiency Tracker

A production-ready internal web application for tracking operational efficiency 
inside the fulfillment center.

### Features:
- 🔐 User authentication (JWT tokens)
- 📦 Batch management (A, B, C, D)
- ⏱️ Real-time operation timing
- 👥 Multi-user support
- 📊 Progress tracking

### Batch Rules:
- **Monday & Thursday**: Batches A, B, C only
- **Other days**: Batches A, B, C, D

### Roles (in order):
1. Procurement
2. Inventory QC - IN
3. QC - Preppers
4. Pre-stagers
5. Extra Service Preppers
6. Pickers and Packers
7. QC-out
8. Stock handler 1
9. Stock handler 2
10. Manifester
11. Driver (requires delivery stats)

### Status Colors:
- 🔴 **RED**: Not started
- 🟡 **YELLOW**: In progress
- 🟢 **GREEN**: Completed
    """,
    version=settings.app_version,
    docs_url="/docs" if settings.debug else "/docs",  # Swagger UI
    redoc_url="/redoc" if settings.debug else "/redoc",  # ReDoc
    openapi_url="/openapi.json",
    lifespan=lifespan,
    
    # Contact info
    contact={
        "name": "Pricepally Tech Team",
        "url": "https://pricepally.com",
    },
    
    # License
    license_info={
        "name": "Proprietary",
    },
)


# ============================================
# CONFIGURE MIDDLEWARE
# ============================================

# Order matters! Last added = first executed

# 1. Request logging (outermost)
if settings.debug:
    configure_logging_middleware(app)

# 2. Security headers
configure_security_middleware(app)

# 3. CORS (must be before routes)
configure_cors(app)


# ============================================
# REGISTER ERROR HANDLERS
# ============================================

register_error_handlers(app)
register_custom_exception_handlers(app)


# ============================================
# REGISTER ROUTERS
# ============================================

# Health check routes (no /api/v1 prefix)
app.include_router(
    health_router,
    prefix="/health",
    tags=["Health"]
)

# Main API routes
app.include_router(api_router)


# ============================================
# ROOT ENDPOINT
# ============================================

@app.get(
    "/",
    tags=["Root"],
    summary="Root endpoint",
    description="Welcome message and API information."
)
async def root():
    """
    Root endpoint with API information.
    """
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health",
        "api": "/api/v1",
        "timestamp": get_current_time().isoformat()
    }


# ============================================
# FAVICON HANDLER (Prevent 404 errors)
# ============================================

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    """Return empty response for favicon requests."""
    return JSONResponse(content={}, status_code=204)


# ============================================
# RUN APPLICATION
# ============================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,  # Auto-reload in debug mode
        log_level="debug" if settings.debug else "info",
        access_log=True,
    )