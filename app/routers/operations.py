# ============================================
# PRICEPALLY OPERATIONS TRACKER
# Operations Router
# ============================================

"""
Operation timing API endpoints.

Endpoints:
- POST /operations/start - Start an operation
- POST /operations/end - Complete an operation
- POST /operations/end-driver - Complete driver operation with stats
- GET /operations/check-previous - Check if previous role is completed
- GET /operations/{date}/{batch}/{role} - Get specific operation
"""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.operation import (
    OperationStart,
    OperationEnd,
    DriverEnd,
    OperationStartResponse,
    OperationEndResponse,
    OperationResponse,
    PreviousRoleCheck,
    AlreadyStartedResponse,
)
from app.services.operation_service import OperationService
from app.middleware.auth_middleware import get_current_user
from app.utils.constants import Messages, VALID_ROLES, VALID_BATCHES
from app.utils.timezone import parse_date


# Create router
router = APIRouter()


# ============================================
# START OPERATION
# ============================================

@router.post(
    "/start",
    response_model=OperationStartResponse,
    summary="Start an operation",
    description="Record the start time for a role in a batch.",
    responses={
        200: {"description": "Operation started successfully"},
        400: {
            "description": "Operation already started or invalid data",
            "model": AlreadyStartedResponse
        },
        401: {"description": "Not authenticated"},
        422: {"description": "Validation error"},
    }
)
async def start_operation(
    data: OperationStart,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Start an operation (record start time).
    
    **Business Rules:**
    - Each role can only be started once per batch/date
    - Timestamps are recorded from server (not client)
    - If previous role is not completed, a warning is returned but operation proceeds
    - Cannot start operations for past dates
    
    **Soft Order Mode:**
    - Roles have a recommended order but can be started in any sequence
    - Warning is shown if starting out of order, but it's allowed
    
    **Returns:**
    - Operation data with start time
    - Optional warning if starting out of order
    """
    success, message, response_data = OperationService.start_operation(
        db=db,
        data=data,
        user=current_user
    )
    
    if not success:
        # Check if it's an "already started" error
        if response_data and response_data.get("error") == "ALREADY_STARTED":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": "ALREADY_STARTED",
                    "message": message,
                    "started_by": response_data.get("started_by"),
                    "started_at": response_data.get("started_at")
                }
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    return OperationStartResponse(
        success=True,
        message=message,
        data=OperationResponse(**response_data["operation"]),
        warning=response_data.get("warning")
    )


# ============================================
# END OPERATION (Non-Driver)
# ============================================

@router.post(
    "/end",
    response_model=OperationEndResponse,
    summary="Complete an operation",
    description="Record the end time for a non-Driver role.",
    responses={
        200: {"description": "Operation completed successfully"},
        400: {"description": "Operation not started or already completed"},
        401: {"description": "Not authenticated"},
        422: {"description": "Validation error"},
    }
)
async def end_operation(
    data: OperationEnd,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Complete an operation (record end time).
    
    **Business Rules:**
    - Operation must be started before it can be completed
    - Once completed, cannot be undone
    - Timestamps are recorded from server (not client)
    - Cannot modify operations for past dates
    
    **Note:** For Driver role, use `/operations/end-driver` endpoint.
    """
    success, message, response_data = OperationService.end_operation(
        db=db,
        data=data,
        user=current_user
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    return OperationEndResponse(
        success=True,
        message=message,
        data=OperationResponse(**response_data["operation"]),
        warning=response_data.get("warning")
    )


# ============================================
# END DRIVER OPERATION
# ============================================

@router.post(
    "/end-driver",
    response_model=OperationEndResponse,
    summary="Complete Driver operation",
    description="Record the end time for Driver role with delivery statistics.",
    responses={
        200: {"description": "Driver operation completed successfully"},
        400: {"description": "Operation not started or already completed"},
        401: {"description": "Not authenticated"},
        422: {"description": "Validation error"},
    }
)
async def end_driver_operation(
    data: DriverEnd,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Complete Driver operation with delivery statistics.
    
    **Required Fields:**
    - total_orders: Total number of orders delivered
    - on_time_deliveries: Number of orders delivered before deadline
    
    **Business Rules:**
    - Driver operation must be started first
    - on_time_deliveries cannot exceed total_orders
    - If other roles are not completed, a warning is returned but operation proceeds
    - Once completed, cannot be undone
    
    **Returns:**
    - Operation data with delivery statistics
    - On-time percentage is automatically calculated
    - Optional warning if other roles are incomplete
    """
    success, message, response_data = OperationService.end_driver_operation(
        db=db,
        data=data,
        user=current_user
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    return OperationEndResponse(
        success=True,
        message=message,
        data=OperationResponse(**response_data["operation"]),
        warning=response_data.get("warning")
    )


# ============================================
# CHECK PREVIOUS ROLE
# ============================================

@router.get(
    "/check-previous",
    response_model=PreviousRoleCheck,
    summary="Check previous role status",
    description="Check if the previous role in sequence is completed.",
    responses={
        200: {"description": "Previous role check result"},
        401: {"description": "Not authenticated"},
        422: {"description": "Validation error"},
    }
)
async def check_previous_role(
    operation_date: date = Query(
        ...,
        description="Operation date (YYYY-MM-DD)",
        example="2024-01-15"
    ),
    batch: str = Query(
        ...,
        min_length=1,
        max_length=1,
        description="Batch identifier (A, B, C, or D)",
        example="A"
    ),
    role: str = Query(
        ...,
        description="Current role name",
        example="QC - Preppers"
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Check if the previous role in the workflow is completed.
    
    **Use Case:**
    Call this before starting a role to check if a warning should be shown.
    
    **Returns:**
    - previous_role: Name of the previous role (null if first role)
    - is_previous_completed: Whether previous role is done
    - show_warning: Whether to show warning to user
    - warning_message: Warning message text (if applicable)
    """
    # Validate inputs
    batch = batch.upper().strip()
    if batch not in VALID_BATCHES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid batch. Must be one of: {', '.join(sorted(VALID_BATCHES))}"
        )
    
    if role not in VALID_ROLES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid role. Must be one of: {', '.join(VALID_ROLES)}"
        )
    
    result = OperationService.check_previous_role(
        db=db,
        operation_date=operation_date,
        batch=batch,
        role=role
    )
    
    return result


# ============================================
# GET SPECIFIC OPERATION
# ============================================

@router.get(
    "/{operation_date}/{batch}/{role}",
    response_model=OperationResponse,
    summary="Get specific operation",
    description="Get details of a specific operation by date, batch, and role.",
    responses={
        200: {"description": "Operation details"},
        404: {"description": "Operation not found"},
        401: {"description": "Not authenticated"},
    }
)
async def get_operation(
    operation_date: date = Path(
        ...,
        description="Operation date (YYYY-MM-DD)",
        example="2024-01-15"
    ),
    batch: str = Path(
        ...,
        min_length=1,
        max_length=1,
        description="Batch identifier",
        example="A"
    ),
    role: str = Path(
        ...,
        description="Role name",
        example="Procurement"
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get details of a specific operation.
    
    **Path Parameters:**
    - operation_date: Date in YYYY-MM-DD format
    - batch: Batch identifier (A, B, C, or D)
    - role: Role name (URL encoded if contains spaces)
    """
    # Validate inputs
    batch = batch.upper().strip()
    if batch not in VALID_BATCHES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid batch. Must be one of: {', '.join(sorted(VALID_BATCHES))}"
        )
    
    if role not in VALID_ROLES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid role. Must be one of: {', '.join(VALID_ROLES)}"
        )
    
    operation = OperationService.get_operation(
        db=db,
        operation_date=operation_date,
        batch=batch,
        role=role
    )
    
    if not operation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Operation not found"
        )
    
    return OperationResponse(
        id=operation.id,
        operation_date=operation.operation_date,
        day_of_week=operation.day_of_week,
        month=operation.month,
        year=operation.year,
        batch=operation.batch,
        operation_role=operation.operation_role,
        status=operation.status,
        start_time=operation.start_time,
        end_time=operation.end_time,
        duration_minutes=operation.duration_minutes,
        total_orders=operation.total_orders,
        on_time_deliveries=operation.on_time_deliveries,
        on_time_percentage=operation.on_time_percentage,
        started_by=operation.started_by_user.name if operation.started_by_user else None,
        completed_by=operation.completed_by_user.name if operation.completed_by_user else None,
    )