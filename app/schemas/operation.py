# ============================================
# PRICEPALLY OPERATIONS TRACKER
# Operation Schemas
# ============================================

"""
Pydantic schemas for operation timing.

Handles:
- Starting operations
- Completing operations
- Driver-specific completion
- Operation status responses
"""

from datetime import date, datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

from app.utils.constants import (
    VALID_ROLES,
    VALID_BATCHES,
    DRIVER_ROLE,
    OperationStatus,
)


# ============================================
# REQUEST SCHEMAS
# ============================================

class OperationStart(BaseModel):
    """
    Schema for starting an operation.
    
    Validates batch and role are valid values.
    """
    
    operation_date: date = Field(
        ...,
        description="Fulfillment operation date (YYYY-MM-DD)",
        examples=["2024-01-15"]
    )
    
    batch: str = Field(
        ...,
        min_length=1,
        max_length=1,
        description="Batch identifier (A, B, C, or D)",
        examples=["A"]
    )
    
    role: str = Field(
        ...,
        description="Operation role name",
        examples=["Procurement"]
    )
    
    @field_validator("batch")
    @classmethod
    def validate_batch(cls, v: str) -> str:
        """Validate batch is A, B, C, or D."""
        v = v.upper().strip()
        if v not in VALID_BATCHES:
            raise ValueError(f"Invalid batch. Must be one of: {', '.join(sorted(VALID_BATCHES))}")
        return v
    
    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        """Validate role is a valid role name."""
        v = v.strip()
        if v not in VALID_ROLES:
            raise ValueError(f"Invalid role. Must be one of: {', '.join(VALID_ROLES)}")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "operation_date": "2024-01-15",
                "batch": "A",
                "role": "Procurement"
            }
        }


class OperationEnd(BaseModel):
    """
    Schema for completing a non-Driver operation.
    """
    
    operation_date: date = Field(
        ...,
        description="Fulfillment operation date (YYYY-MM-DD)",
        examples=["2024-01-15"]
    )
    
    batch: str = Field(
        ...,
        min_length=1,
        max_length=1,
        description="Batch identifier (A, B, C, or D)",
        examples=["A"]
    )
    
    role: str = Field(
        ...,
        description="Operation role name",
        examples=["Procurement"]
    )
    
    @field_validator("batch")
    @classmethod
    def validate_batch(cls, v: str) -> str:
        """Validate batch is A, B, C, or D."""
        v = v.upper().strip()
        if v not in VALID_BATCHES:
            raise ValueError(f"Invalid batch. Must be one of: {', '.join(sorted(VALID_BATCHES))}")
        return v
    
    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        """Validate role is a valid role name (excluding Driver)."""
        v = v.strip()
        if v not in VALID_ROLES:
            raise ValueError(f"Invalid role. Must be one of: {', '.join(VALID_ROLES)}")
        if v == DRIVER_ROLE:
            raise ValueError("Use /operations/end-driver endpoint for Driver role")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "operation_date": "2024-01-15",
                "batch": "A",
                "role": "Procurement"
            }
        }


class DriverEnd(BaseModel):
    """
    Schema for completing Driver operation.
    
    Requires additional delivery statistics.
    """
    
    operation_date: date = Field(
        ...,
        description="Fulfillment operation date (YYYY-MM-DD)",
        examples=["2024-01-15"]
    )
    
    batch: str = Field(
        ...,
        min_length=1,
        max_length=1,
        description="Batch identifier (A, B, C, or D)",
        examples=["A"]
    )
    
    total_orders: int = Field(
        ...,
        ge=0,
        description="Total number of orders delivered",
        examples=[150]
    )
    
    on_time_deliveries: int = Field(
        ...,
        ge=0,
        description="Number of orders delivered before deadline",
        examples=[142]
    )
    
    @field_validator("batch")
    @classmethod
    def validate_batch(cls, v: str) -> str:
        """Validate batch is A, B, C, or D."""
        v = v.upper().strip()
        if v not in VALID_BATCHES:
            raise ValueError(f"Invalid batch. Must be one of: {', '.join(sorted(VALID_BATCHES))}")
        return v
    
    @model_validator(mode="after")
    def validate_order_counts(self):
        """Validate on_time_deliveries doesn't exceed total_orders."""
        if self.on_time_deliveries > self.total_orders:
            raise ValueError("On-time deliveries cannot exceed total orders")
        return self
    
    class Config:
        json_schema_extra = {
            "example": {
                "operation_date": "2024-01-15",
                "batch": "A",
                "total_orders": 150,
                "on_time_deliveries": 142
            }
        }


# ============================================
# RESPONSE SCHEMAS
# ============================================

class OperationResponse(BaseModel):
    """
    Schema for operation data in responses.
    """
    
    id: UUID = Field(
        ...,
        description="Unique operation identifier"
    )
    
    operation_date: date = Field(
        ...,
        description="Fulfillment operation date"
    )
    
    day_of_week: str = Field(
        ...,
        description="Day name (Monday, Tuesday, etc.)"
    )
    
    month: str = Field(
        ...,
        description="Month name (January, February, etc.)"
    )
    
    year: int = Field(
        ...,
        description="Year"
    )
    
    batch: str = Field(
        ...,
        description="Batch identifier"
    )
    
    operation_role: str = Field(
        ...,
        description="Role name"
    )
    
    status: str = Field(
        ...,
        description="Current status (PENDING, IN_PROGRESS, COMPLETED)"
    )
    
    start_time: Optional[datetime] = Field(
        default=None,
        description="When role started"
    )
    
    end_time: Optional[datetime] = Field(
        default=None,
        description="When role completed"
    )
    
    duration_minutes: Optional[int] = Field(
        default=None,
        description="Duration in minutes (if completed)"
    )
    
    total_orders: Optional[int] = Field(
        default=None,
        description="Driver: Total orders delivered"
    )
    
    on_time_deliveries: Optional[int] = Field(
        default=None,
        description="Driver: Orders delivered on time"
    )
    
    on_time_percentage: Optional[float] = Field(
        default=None,
        description="Driver: Percentage of on-time deliveries"
    )
    
    started_by: Optional[str] = Field(
        default=None,
        description="Name of user who started"
    )
    
    completed_by: Optional[str] = Field(
        default=None,
        description="Name of user who completed"
    )
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "operation_date": "2024-01-15",
                "day_of_week": "Monday",
                "month": "January",
                "year": 2024,
                "batch": "A",
                "operation_role": "Procurement",
                "status": "COMPLETED",
                "start_time": "2024-01-15T08:00:00+01:00",
                "end_time": "2024-01-15T09:30:00+01:00",
                "duration_minutes": 90,
                "total_orders": None,
                "on_time_deliveries": None,
                "on_time_percentage": None,
                "started_by": "John Doe",
                "completed_by": "John Doe"
            }
        }


class OperationStartResponse(BaseModel):
    """
    Response after starting an operation.
    """
    
    success: bool = Field(
        default=True,
        description="Whether the operation was successful"
    )
    
    message: str = Field(
        ...,
        description="Response message"
    )
    
    data: OperationResponse = Field(
        ...,
        description="Operation data"
    )
    
    warning: Optional[str] = Field(
        default=None,
        description="Warning message (e.g., previous operation not completed)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Operation started successfully",
                "data": {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "operation_date": "2024-01-15",
                    "day_of_week": "Monday",
                    "month": "January",
                    "year": 2024,
                    "batch": "A",
                    "operation_role": "QC - Preppers",
                    "status": "IN_PROGRESS",
                    "start_time": "2024-01-15T10:00:00+01:00",
                    "end_time": None,
                    "duration_minutes": None,
                    "started_by": "John Doe",
                    "completed_by": None
                },
                "warning": "Previous operation not completed yet"
            }
        }


class OperationEndResponse(BaseModel):
    """
    Response after completing an operation.
    """
    
    success: bool = Field(
        default=True,
        description="Whether the operation was successful"
    )
    
    message: str = Field(
        ...,
        description="Response message"
    )
    
    data: OperationResponse = Field(
        ...,
        description="Operation data"
    )
    
    warning: Optional[str] = Field(
        default=None,
        description="Warning message (e.g., some roles not completed)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Operation completed successfully",
                "data": {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "operation_date": "2024-01-15",
                    "day_of_week": "Monday",
                    "month": "January",
                    "year": 2024,
                    "batch": "A",
                    "operation_role": "Procurement",
                    "status": "COMPLETED",
                    "start_time": "2024-01-15T08:00:00+01:00",
                    "end_time": "2024-01-15T09:30:00+01:00",
                    "duration_minutes": 90,
                    "started_by": "John Doe",
                    "completed_by": "Jane Doe"
                },
                "warning": None
            }
        }


class RoleStatusResponse(BaseModel):
    """
    Status of a single role within a batch.
    """
    
    role: str = Field(
        ...,
        description="Role name"
    )
    
    order: int = Field(
        ...,
        description="Role order in workflow (1-11)"
    )
    
    status: str = Field(
        ...,
        description="Current status (PENDING, IN_PROGRESS, COMPLETED)"
    )
    
    start_time: Optional[datetime] = Field(
        default=None,
        description="When role started"
    )
    
    end_time: Optional[datetime] = Field(
        default=None,
        description="When role completed"
    )
    
    duration_minutes: Optional[int] = Field(
        default=None,
        description="Duration in minutes"
    )
    
    started_by: Optional[str] = Field(
        default=None,
        description="Name of user who started"
    )
    
    completed_by: Optional[str] = Field(
        default=None,
        description="Name of user who completed"
    )
    
    # Driver-specific fields
    total_orders: Optional[int] = Field(
        default=None,
        description="Driver: Total orders"
    )
    
    on_time_deliveries: Optional[int] = Field(
        default=None,
        description="Driver: On-time deliveries"
    )
    
    on_time_percentage: Optional[float] = Field(
        default=None,
        description="Driver: On-time percentage"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "role": "Procurement",
                "order": 1,
                "status": "COMPLETED",
                "start_time": "2024-01-15T08:00:00+01:00",
                "end_time": "2024-01-15T09:30:00+01:00",
                "duration_minutes": 90,
                "started_by": "John Doe",
                "completed_by": "John Doe",
                "total_orders": None,
                "on_time_deliveries": None,
                "on_time_percentage": None
            }
        }


class PreviousRoleCheck(BaseModel):
    """
    Response for checking if previous role is completed.
    
    Used to show warning when starting a role out of order.
    """
    
    current_role: str = Field(
        ...,
        description="Role being checked"
    )
    
    previous_role: Optional[str] = Field(
        default=None,
        description="Previous role in sequence (None if first)"
    )
    
    is_previous_completed: bool = Field(
        ...,
        description="Whether previous role is completed"
    )
    
    show_warning: bool = Field(
        ...,
        description="Whether to show warning to user"
    )
    
    warning_message: Optional[str] = Field(
        default=None,
        description="Warning message if applicable"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "current_role": "QC - Preppers",
                "previous_role": "Inventory QC - IN",
                "is_previous_completed": False,
                "show_warning": True,
                "warning_message": "Previous operation 'Inventory QC - IN' not completed yet. Continue anyway?"
            }
        }


class AlreadyStartedResponse(BaseModel):
    """
    Response when trying to start an already-started operation.
    """
    
    success: bool = Field(
        default=False,
        description="Always False for this error"
    )
    
    error: str = Field(
        default="ALREADY_STARTED",
        description="Error code"
    )
    
    message: str = Field(
        ...,
        description="Error message"
    )
    
    started_by: str = Field(
        ...,
        description="Name of user who already started it"
    )
    
    started_at: datetime = Field(
        ...,
        description="When it was started"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error": "ALREADY_STARTED",
                "message": "Operation already started",
                "started_by": "Jane Doe",
                "started_at": "2024-01-15T08:00:00+01:00"
            }
        }