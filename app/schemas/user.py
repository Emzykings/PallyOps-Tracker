# ============================================
# PRICEPALLY OPERATIONS TRACKER
# User Schemas
# ============================================

"""
Pydantic schemas for user authentication.

Handles:
- User registration
- User login
- Token responses
- User data serialization
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.utils.constants import MIN_PASSWORD_LENGTH, PASSWORD_REQUIREMENTS
from app.utils.security import validate_password_strength, validate_name


# ============================================
# REQUEST SCHEMAS
# ============================================

class UserCreate(BaseModel):
    """
    Schema for user registration request.
    
    Validates:
    - Name (2-100 characters)
    - Email (valid format)
    - Password (meets security requirements)
    """
    
    name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="User's display name",
        examples=["John Doe"]
    )
    
    email: EmailStr = Field(
        ...,
        description="User's email address",
        examples=["john.doe@pricepally.com"]
    )
    
    password: str = Field(
        ...,
        min_length=MIN_PASSWORD_LENGTH,
        max_length=128,
        description=PASSWORD_REQUIREMENTS,
        examples=["SecurePass123"]
    )
    
    @field_validator("name")
    @classmethod
    def validate_name_field(cls, v: str) -> str:
        """Validate and sanitize name."""
        v = v.strip()
        is_valid, error = validate_name(v)
        if not is_valid:
            raise ValueError(error)
        return v
    
    @field_validator("password")
    @classmethod
    def validate_password_field(cls, v: str) -> str:
        """Validate password meets security requirements."""
        is_valid, error = validate_password_strength(v)
        if not is_valid:
            raise ValueError(error)
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "John Doe",
                "email": "john.doe@pricepally.com",
                "password": "SecurePass123"
            }
        }


class UserLogin(BaseModel):
    """
    Schema for user login request.
    
    Simple email and password validation.
    """
    
    email: EmailStr = Field(
        ...,
        description="User's email address",
        examples=["john.doe@pricepally.com"]
    )
    
    password: str = Field(
        ...,
        min_length=1,
        description="User's password",
        examples=["SecurePass123"]
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "john.doe@pricepally.com",
                "password": "SecurePass123"
            }
        }


# ============================================
# RESPONSE SCHEMAS
# ============================================

class UserResponse(BaseModel):
    """
    Schema for user data in responses.
    
    Excludes sensitive data like password hash.
    """
    
    id: UUID = Field(
        ...,
        description="Unique user identifier"
    )
    
    name: str = Field(
        ...,
        description="User's display name"
    )
    
    email: EmailStr = Field(
        ...,
        description="User's email address"
    )
    
    created_at: datetime = Field(
        ...,
        description="Account creation timestamp"
    )
    
    class Config:
        from_attributes = True  # Allow ORM model conversion
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "John Doe",
                "email": "john.doe@pricepally.com",
                "created_at": "2024-01-15T10:30:00+01:00"
            }
        }


class TokenResponse(BaseModel):
    """
    Schema for JWT token response.
    """
    
    access_token: str = Field(
        ...,
        description="JWT access token"
    )
    
    token_type: str = Field(
        default="bearer",
        description="Token type (always 'bearer')"
    )
    
    expires_in: int = Field(
        ...,
        description="Token expiration time in seconds"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 86400
            }
        }


class AuthResponse(BaseModel):
    """
    Schema for authentication response (login/register).
    
    Combines user data and token.
    """
    
    success: bool = Field(
        default=True,
        description="Whether the request was successful"
    )
    
    message: str = Field(
        ...,
        description="Response message"
    )
    
    user: UserResponse = Field(
        ...,
        description="User data"
    )
    
    token: TokenResponse = Field(
        ...,
        description="JWT token data"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Login successful",
                "user": {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "name": "John Doe",
                    "email": "john.doe@pricepally.com",
                    "created_at": "2024-01-15T10:30:00+01:00"
                },
                "token": {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "token_type": "bearer",
                    "expires_in": 86400
                }
            }
        }


# ============================================
# INTERNAL SCHEMAS
# ============================================

class UserInDB(UserResponse):
    """
    Schema for user data including password hash.
    
    Used internally, never exposed in API responses.
    """
    
    password_hash: str = Field(
        ...,
        description="Bcrypt hashed password"
    )


# ============================================
# SIMPLE RESPONSE SCHEMAS
# ============================================

class MessageResponse(BaseModel):
    """
    Simple message response schema.
    """
    
    success: bool = Field(
        default=True,
        description="Whether the request was successful"
    )
    
    message: str = Field(
        ...,
        description="Response message"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Operation completed successfully"
            }
        }


class ErrorResponse(BaseModel):
    """
    Error response schema.
    """
    
    success: bool = Field(
        default=False,
        description="Always False for errors"
    )
    
    error: str = Field(
        ...,
        description="Error type"
    )
    
    message: str = Field(
        ...,
        description="Error message"
    )
    
    detail: Optional[str] = Field(
        default=None,
        description="Additional error details"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error": "ValidationError",
                "message": "Invalid input data",
                "detail": "Email already exists"
            }
        }