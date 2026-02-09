# ============================================
# PRICEPALLY OPERATIONS TRACKER
# Schemas Package Initialization
# ============================================

"""
Pydantic schemas for request validation and response serialization.

This package contains:
- user: User authentication schemas
- operation: Operation timing schemas
- batch: Batch management schemas
"""

from app.schemas.user import (
    UserCreate,
    UserLogin,
    UserResponse,
    UserInDB,
    TokenResponse,
    AuthResponse,
)
from app.schemas.operation import (
    OperationStart,
    OperationEnd,
    DriverEnd,
    OperationResponse,
    OperationStartResponse,
    OperationEndResponse,
    RoleStatusResponse,
    PreviousRoleCheck,
)
from app.schemas.batch import (
    BatchStatusResponse,
    BatchListResponse,
    BatchDetailResponse,
    BatchRolesResponse,
)

__all__ = [
    # User schemas
    "UserCreate",
    "UserLogin",
    "UserResponse",
    "UserInDB",
    "TokenResponse",
    "AuthResponse",
    # Operation schemas
    "OperationStart",
    "OperationEnd",
    "DriverEnd",
    "OperationResponse",
    "OperationStartResponse",
    "OperationEndResponse",
    "RoleStatusResponse",
    "PreviousRoleCheck",
    # Batch schemas
    "BatchStatusResponse",
    "BatchListResponse",
    "BatchDetailResponse",
    "BatchRolesResponse",
]