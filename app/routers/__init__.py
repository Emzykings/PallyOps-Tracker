# ============================================
# PRICEPALLY OPERATIONS TRACKER
# Routers Package Initialization
# ============================================

"""
API route handlers.

This package contains:
- auth: Authentication endpoints (register, login, logout)
- operations: Operation timing endpoints (start, end)
- batches: Batch management endpoints (list, details)
- health: Health check endpoints
"""

from fastapi import APIRouter

from app.routers.auth import router as auth_router
from app.routers.operations import router as operations_router
from app.routers.batches import router as batches_router
from app.routers.health import router as health_router


# Create main API router
api_router = APIRouter(prefix="/api/v1")

# Include all sub-routers
api_router.include_router(
    auth_router,
    prefix="/auth",
    tags=["Authentication"]
)

api_router.include_router(
    operations_router,
    prefix="/operations",
    tags=["Operations"]
)

api_router.include_router(
    batches_router,
    prefix="/batches",
    tags=["Batches"]
)

# Health check at root level (no /api/v1 prefix)
# This is included separately in main.py


__all__ = [
    "api_router",
    "auth_router",
    "operations_router",
    "batches_router",
    "health_router",
]