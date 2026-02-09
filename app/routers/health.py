# ============================================
# PRICEPALLY OPERATIONS TRACKER
# Health Check Router
# ============================================

"""
Health check endpoints for monitoring and deployment.

Endpoints:
- GET /health - Basic health check
- GET /health/ready - Readiness check (includes database)
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import get_db
from app.config import settings
from app.utils.timezone import get_current_time


# Create router
router = APIRouter()


# ============================================
# BASIC HEALTH CHECK
# ============================================

@router.get(
    "",
    summary="Health check",
    description="Basic health check endpoint.",
    responses={
        200: {"description": "Service is healthy"},
    }
)
async def health_check():
    """
    Basic health check.
    
    Returns service status and version.
    Used by load balancers and monitoring systems.
    """
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
        "timestamp": get_current_time().isoformat()
    }


# ============================================
# READINESS CHECK
# ============================================

@router.get(
    "/ready",
    summary="Readiness check",
    description="Check if the service is ready to accept requests.",
    responses={
        200: {"description": "Service is ready"},
        503: {"description": "Service is not ready"},
    }
)
async def readiness_check(db: Session = Depends(get_db)):
    """
    Readiness check including database connectivity.
    
    Checks:
    - Database connection is working
    
    Used by Kubernetes/Docker for readiness probes.
    """
    checks = {
        "database": False
    }
    
    # Check database
    try:
        db.execute(text("SELECT 1"))
        checks["database"] = True
    except Exception as e:
        checks["database"] = False
        checks["database_error"] = str(e)
    
    # Determine overall status
    all_healthy = all([
        checks["database"]
    ])
    
    return {
        "status": "ready" if all_healthy else "not_ready",
        "checks": checks,
        "timestamp": get_current_time().isoformat()
    }


# ============================================
# DETAILED INFO (Debug only)
# ============================================

@router.get(
    "/info",
    summary="Service info",
    description="Get detailed service information (debug mode only).",
    responses={
        200: {"description": "Service information"},
        403: {"description": "Not available in production"},
    }
)
async def service_info():
    """
    Get detailed service information.
    
    Only available when DEBUG=True.
    """
    if not settings.debug:
        return {
            "message": "Info endpoint not available in production"
        }
    
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "debug": settings.debug,
        "timezone": settings.timezone,
        "timestamp": get_current_time().isoformat()
    }