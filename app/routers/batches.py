# ============================================
# PRICEPALLY OPERATIONS TRACKER
# Batches Router
# ============================================

"""
Batch management API endpoints.

Endpoints:
- GET /batches - Get all batches for a date
- GET /batches/{batch} - Get batch details
- GET /batches/{batch}/roles - Get batch with all role statuses
- GET /batches/summary - Get daily summary
"""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.batch import (
    BatchListResponse,
    BatchDetailResponse,
    BatchRolesResponse,
    DailySummary,
)
from app.services.batch_service import BatchService
from app.middleware.auth_middleware import get_current_user
from app.utils.constants import VALID_BATCHES, get_available_batches_for_date


# Create router
router = APIRouter()


# ============================================
# GET BATCHES FOR DATE
# ============================================

@router.get(
    "",
    response_model=BatchListResponse,
    summary="Get batches for date",
    description="Get all available batches with their status for a specific date.",
    responses={
        200: {"description": "List of batches with status"},
        401: {"description": "Not authenticated"},
        422: {"description": "Validation error"},
    }
)
async def get_batches(
    operation_date: date = Query(
        ...,
        description="Operation date (YYYY-MM-DD)",
        example="2024-01-15"
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all available batches for a date with their current status.
    
    **Batch Availability:**
    - Monday and Thursday: Batches A, B, C only (no D)
    - Other days: Batches A, B, C, D
    
    **Status Colors:**
    - RED: No roles have been started
    - YELLOW: Some roles started or in progress
    - GREEN: All 11 roles completed
    
    **Returns:**
    - List of batches with status and progress information
    - Whether it's a restricted day (Mon/Thu)
    """
    result = BatchService.get_batches_for_date(db, operation_date)
    return result


# ============================================
# GET BATCH DETAILS
# ============================================

@router.get(
    "/{batch}",
    response_model=BatchDetailResponse,
    summary="Get batch details",
    description="Get detailed information about a specific batch.",
    responses={
        200: {"description": "Batch details"},
        404: {"description": "Batch not found or not available for date"},
        401: {"description": "Not authenticated"},
        422: {"description": "Validation error"},
    }
)
async def get_batch_detail(
    batch: str = Path(
        ...,
        min_length=1,
        max_length=1,
        description="Batch identifier (A, B, C, or D)",
        example="A"
    ),
    operation_date: date = Query(
        ...,
        description="Operation date (YYYY-MM-DD)",
        example="2024-01-15"
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific batch.
    
    **Returns:**
    - Batch status (RED/YELLOW/GREEN)
    - Progress counts (started, completed, total)
    - Progress percentage
    - Whether the date is read-only (past dates)
    """
    # Validate batch
    batch = batch.upper().strip()
    if batch not in VALID_BATCHES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid batch. Must be one of: {', '.join(sorted(VALID_BATCHES))}"
        )
    
    result = BatchService.get_batch_detail(db, operation_date, batch)
    
    if result is None:
        available = get_available_batches_for_date(operation_date)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch {batch} is not available for this date. Available batches: {', '.join(available)}"
        )
    
    return result


# ============================================
# GET BATCH WITH ALL ROLES
# ============================================

@router.get(
    "/{batch}/roles",
    response_model=BatchRolesResponse,
    summary="Get batch with roles",
    description="Get batch details with all role statuses for the workflow page.",
    responses={
        200: {"description": "Batch with all roles"},
        404: {"description": "Batch not found or not available for date"},
        401: {"description": "Not authenticated"},
        422: {"description": "Validation error"},
    }
)
async def get_batch_roles(
    batch: str = Path(
        ...,
        min_length=1,
        max_length=1,
        description="Batch identifier (A, B, C, or D)",
        example="A"
    ),
    operation_date: date = Query(
        ...,
        description="Operation date (YYYY-MM-DD)",
        example="2024-01-15"
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get batch with all role statuses.
    
    **Use Case:**
    This endpoint powers the batch workflow page, showing all 11 roles
    with their current status.
    
    **Returns:**
    - Batch information
    - List of all 11 roles in order with:
        - Role name and order number
        - Status (PENDING/IN_PROGRESS/COMPLETED)
        - Start/end times
        - Duration (if completed)
        - Who started/completed it
        - Driver stats (if applicable)
    - Whether the date is read-only (past dates)
    """
    # Validate batch
    batch = batch.upper().strip()
    if batch not in VALID_BATCHES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid batch. Must be one of: {', '.join(sorted(VALID_BATCHES))}"
        )
    
    result = BatchService.get_batch_with_roles(db, operation_date, batch)
    
    if result is None:
        available = get_available_batches_for_date(operation_date)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch {batch} is not available for this date. Available batches: {', '.join(available)}"
        )
    
    return result


# ============================================
# GET DAILY SUMMARY
# ============================================

@router.get(
    "/summary/daily",
    response_model=DailySummary,
    summary="Get daily summary",
    description="Get summary statistics for a specific date.",
    responses={
        200: {"description": "Daily summary statistics"},
        401: {"description": "Not authenticated"},
        422: {"description": "Validation error"},
    }
)
async def get_daily_summary(
    operation_date: date = Query(
        ...,
        description="Operation date (YYYY-MM-DD)",
        example="2024-01-15"
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get summary statistics for a day.
    
    **Returns:**
    - Total and completed batches
    - Total and completed roles
    - Overall progress percentage
    - Total orders delivered (from all Driver operations)
    - Total on-time deliveries
    - Overall on-time percentage
    """
    summary = BatchService.get_daily_summary(db, operation_date)
    
    return DailySummary(**summary)


# ============================================
# INITIALIZE BATCH (Optional utility endpoint)
# ============================================

@router.post(
    "/{batch}/initialize",
    response_model=BatchRolesResponse,
    summary="Initialize batch",
    description="Pre-create all role records for a batch (optional utility).",
    responses={
        200: {"description": "Batch initialized"},
        400: {"description": "Batch not available for date"},
        401: {"description": "Not authenticated"},
        422: {"description": "Validation error"},
    }
)
async def initialize_batch(
    batch: str = Path(
        ...,
        min_length=1,
        max_length=1,
        description="Batch identifier (A, B, C, or D)",
        example="A"
    ),
    operation_date: date = Query(
        ...,
        description="Operation date (YYYY-MM-DD)",
        example="2024-01-15"
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Initialize all role records for a batch.
    
    **Note:** This is optional. Role records are automatically created
    when starting an operation. This endpoint can be used to pre-populate
    batch data for display purposes.
    
    **Returns:**
    - Batch with all roles in PENDING status
    """
    # Validate batch
    batch = batch.upper().strip()
    if batch not in VALID_BATCHES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid batch. Must be one of: {', '.join(sorted(VALID_BATCHES))}"
        )
    
    # Check if batch is available for this date
    if not BatchService.is_batch_available(operation_date, batch):
        available = get_available_batches_for_date(operation_date)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Batch {batch} is not available for this date. Available batches: {', '.join(available)}"
        )
    
    # Initialize the batch
    success = BatchService.initialize_batch(db, operation_date, batch)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initialize batch"
        )
    
    # Return the batch with roles
    result = BatchService.get_batch_with_roles(db, operation_date, batch)
    return result