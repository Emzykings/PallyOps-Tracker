# ============================================
# PRICEPALLY OPERATIONS TRACKER
# Batch Schemas
# ============================================

"""
Pydantic schemas for batch management.

Handles:
- Batch listing
- Batch status
- Batch details with roles
"""

from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.operation import RoleStatusResponse
from app.utils.constants import BatchStatus


# ============================================
# BATCH STATUS SCHEMAS
# ============================================

class BatchStatusResponse(BaseModel):
    """
    Status of a single batch.
    """
    
    batch: str = Field(
        ...,
        description="Batch identifier (A, B, C, or D)"
    )
    
    status: str = Field(
        ...,
        description=f"Batch status ({BatchStatus.RED}, {BatchStatus.YELLOW}, {BatchStatus.GREEN})"
    )
    
    started_count: int = Field(
        ...,
        description="Number of roles started"
    )
    
    completed_count: int = Field(
        ...,
        description="Number of roles completed"
    )
    
    total_roles: int = Field(
        ...,
        description="Total number of roles (always 11)"
    )
    
    progress_percentage: float = Field(
        ...,
        description="Completion percentage (0-100)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "batch": "A",
                "status": "YELLOW",
                "started_count": 5,
                "completed_count": 3,
                "total_roles": 11,
                "progress_percentage": 27.27
            }
        }


class BatchListResponse(BaseModel):
    """
    Response for listing all batches for a date.
    """
    
    success: bool = Field(
        default=True,
        description="Whether the request was successful"
    )
    
    operation_date: date = Field(
        ...,
        description="The operation date"
    )
    
    day_of_week: str = Field(
        ...,
        description="Day name (Monday, Tuesday, etc.)"
    )
    
    is_restricted_day: bool = Field(
        ...,
        description="True if Monday or Thursday (no Batch D)"
    )
    
    batches: List[BatchStatusResponse] = Field(
        ...,
        description="List of batch statuses"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "operation_date": "2024-01-15",
                "day_of_week": "Monday",
                "is_restricted_day": True,
                "batches": [
                    {
                        "batch": "A",
                        "status": "GREEN",
                        "started_count": 11,
                        "completed_count": 11,
                        "total_roles": 11,
                        "progress_percentage": 100.0
                    },
                    {
                        "batch": "B",
                        "status": "YELLOW",
                        "started_count": 5,
                        "completed_count": 3,
                        "total_roles": 11,
                        "progress_percentage": 27.27
                    },
                    {
                        "batch": "C",
                        "status": "RED",
                        "started_count": 0,
                        "completed_count": 0,
                        "total_roles": 11,
                        "progress_percentage": 0.0
                    }
                ]
            }
        }


class BatchDetailResponse(BaseModel):
    """
    Detailed batch information with all roles.
    """
    
    success: bool = Field(
        default=True,
        description="Whether the request was successful"
    )
    
    batch: str = Field(
        ...,
        description="Batch identifier"
    )
    
    operation_date: date = Field(
        ...,
        description="The operation date"
    )
    
    day_of_week: str = Field(
        ...,
        description="Day name"
    )
    
    status: str = Field(
        ...,
        description="Overall batch status"
    )
    
    is_readonly: bool = Field(
        ...,
        description="True if past date (no modifications allowed)"
    )
    
    started_count: int = Field(
        ...,
        description="Number of roles started"
    )
    
    completed_count: int = Field(
        ...,
        description="Number of roles completed"
    )
    
    total_roles: int = Field(
        ...,
        description="Total number of roles"
    )
    
    progress_percentage: float = Field(
        ...,
        description="Completion percentage"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "batch": "A",
                "operation_date": "2024-01-15",
                "day_of_week": "Monday",
                "status": "YELLOW",
                "is_readonly": False,
                "started_count": 5,
                "completed_count": 3,
                "total_roles": 11,
                "progress_percentage": 27.27
            }
        }


class BatchRolesResponse(BaseModel):
    """
    Complete batch data with all role statuses.
    
    Used for the batch workflow page.
    """
    
    success: bool = Field(
        default=True,
        description="Whether the request was successful"
    )
    
    batch: str = Field(
        ...,
        description="Batch identifier"
    )
    
    operation_date: date = Field(
        ...,
        description="The operation date"
    )
    
    day_of_week: str = Field(
        ...,
        description="Day name"
    )
    
    month: str = Field(
        ...,
        description="Month name"
    )
    
    year: int = Field(
        ...,
        description="Year"
    )
    
    status: str = Field(
        ...,
        description="Overall batch status"
    )
    
    is_readonly: bool = Field(
        ...,
        description="True if past date (no modifications allowed)"
    )
    
    started_count: int = Field(
        ...,
        description="Number of roles started"
    )
    
    completed_count: int = Field(
        ...,
        description="Number of roles completed"
    )
    
    total_roles: int = Field(
        ...,
        description="Total number of roles"
    )
    
    progress_percentage: float = Field(
        ...,
        description="Completion percentage"
    )
    
    roles: List[RoleStatusResponse] = Field(
        ...,
        description="List of all roles with their statuses"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "batch": "A",
                "operation_date": "2024-01-15",
                "day_of_week": "Monday",
                "month": "January",
                "year": 2024,
                "status": "YELLOW",
                "is_readonly": False,
                "started_count": 5,
                "completed_count": 3,
                "total_roles": 11,
                "progress_percentage": 27.27,
                "roles": [
                    {
                        "role": "Procurement",
                        "order": 1,
                        "status": "COMPLETED",
                        "start_time": "2024-01-15T08:00:00+01:00",
                        "end_time": "2024-01-15T09:30:00+01:00",
                        "duration_minutes": 90,
                        "started_by": "John Doe",
                        "completed_by": "John Doe"
                    },
                    {
                        "role": "Inventory QC - IN",
                        "order": 2,
                        "status": "IN_PROGRESS",
                        "start_time": "2024-01-15T09:35:00+01:00",
                        "end_time": None,
                        "duration_minutes": None,
                        "started_by": "Jane Doe",
                        "completed_by": None
                    },
                    {
                        "role": "QC - Preppers",
                        "order": 3,
                        "status": "PENDING",
                        "start_time": None,
                        "end_time": None,
                        "duration_minutes": None,
                        "started_by": None,
                        "completed_by": None
                    }
                ]
            }
        }


# ============================================
# QUERY PARAMETER SCHEMAS
# ============================================

class DateQuery(BaseModel):
    """
    Query parameters for date-based requests.
    """
    
    operation_date: date = Field(
        ...,
        description="Operation date in YYYY-MM-DD format",
        examples=["2024-01-15"]
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "operation_date": "2024-01-15"
            }
        }


# ============================================
# SUMMARY SCHEMAS (for analytics)
# ============================================

class DailySummary(BaseModel):
    """
    Summary of operations for a single day.
    
    Useful for analytics and reporting.
    """
    
    operation_date: date = Field(
        ...,
        description="The operation date"
    )
    
    day_of_week: str = Field(
        ...,
        description="Day name"
    )
    
    total_batches: int = Field(
        ...,
        description="Number of batches for this day"
    )
    
    completed_batches: int = Field(
        ...,
        description="Number of fully completed batches"
    )
    
    total_roles: int = Field(
        ...,
        description="Total role slots (batches × 11)"
    )
    
    completed_roles: int = Field(
        ...,
        description="Number of completed roles"
    )
    
    overall_progress: float = Field(
        ...,
        description="Overall completion percentage"
    )
    
    total_orders_delivered: Optional[int] = Field(
        default=None,
        description="Sum of all driver orders"
    )
    
    total_on_time_deliveries: Optional[int] = Field(
        default=None,
        description="Sum of all on-time deliveries"
    )
    
    overall_on_time_percentage: Optional[float] = Field(
        default=None,
        description="Overall on-time percentage"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "operation_date": "2024-01-15",
                "day_of_week": "Monday",
                "total_batches": 3,
                "completed_batches": 2,
                "total_roles": 33,
                "completed_roles": 28,
                "overall_progress": 84.85,
                "total_orders_delivered": 450,
                "total_on_time_deliveries": 425,
                "overall_on_time_percentage": 94.44
            }
        }