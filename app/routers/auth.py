# ============================================
# PRICEPALLY OPERATIONS TRACKER
# Authentication Router
# ============================================

"""
Authentication API endpoints.

Endpoints:
- POST /auth/register - Create new user account
- POST /auth/login - Login and get token
- POST /auth/logout - Logout and invalidate token
- GET /auth/me - Get current user info
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.user import (
    UserCreate,
    UserLogin,
    UserResponse,
    AuthResponse,
    MessageResponse,
    ErrorResponse,
)
from app.services.auth_service import AuthService
from app.middleware.auth_middleware import get_current_user, oauth2_scheme
from app.utils.constants import Messages


# Create router
router = APIRouter()


# ============================================
# REGISTER
# ============================================

@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
    description="Create a new user account and return authentication token.",
    responses={
        201: {"description": "User created successfully"},
        400: {"description": "Invalid input or email already exists"},
        422: {"description": "Validation error"},
    }
)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Register a new user account.
    
    **Requirements:**
    - Name: 2-100 characters
    - Email: Valid email format, unique
    - Password: Min 8 chars, 1 uppercase, 1 lowercase, 1 number
    
    **Returns:**
    - User information
    - JWT access token (valid for 24 hours)
    """
    success, message, response = AuthService.register_user(db, user_data)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    return response


# ============================================
# LOGIN
# ============================================

@router.post(
    "/login",
    response_model=AuthResponse,
    summary="Login user",
    description="Authenticate user and return access token.",
    responses={
        200: {"description": "Login successful"},
        401: {"description": "Invalid credentials"},
        422: {"description": "Validation error"},
    }
)
async def login(
    login_data: UserLogin,
    db: Session = Depends(get_db)
):
    """
    Login with email and password.
    
    **Returns:**
    - User information
    - JWT access token (valid for 24 hours)
    
    **Usage:**
    Include token in subsequent requests:
    ```
    Authorization: Bearer <access_token>
    ```
    """
    success, message, response = AuthService.login_user(db, login_data)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=message,
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return response


# ============================================
# LOGIN (OAuth2 Form - for Swagger UI)
# ============================================

@router.post(
    "/login/form",
    response_model=AuthResponse,
    summary="Login user (Form)",
    description="Login using OAuth2 form format (for Swagger UI testing).",
    include_in_schema=False  # Hide from docs, just for Swagger
)
async def login_form(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Login using OAuth2 password form.
    
    This endpoint exists for Swagger UI's "Authorize" button.
    Use /login for normal API requests.
    """
    login_data = UserLogin(
        email=form_data.username,  # OAuth2 uses "username" field
        password=form_data.password
    )
    
    success, message, response = AuthService.login_user(db, login_data)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=message,
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return response


# ============================================
# LOGOUT
# ============================================

@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Logout user",
    description="Invalidate current access token.",
    responses={
        200: {"description": "Logout successful"},
        401: {"description": "Not authenticated"},
    }
)
async def logout(
    current_user: User = Depends(get_current_user),
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """
    Logout and invalidate the current token.
    
    After logout, the token can no longer be used for authentication.
    """
    success, message = AuthService.logout_user(db, token, current_user.id)
    
    return MessageResponse(
        success=success,
        message=message
    )


# ============================================
# GET CURRENT USER
# ============================================

@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
    description="Get information about the currently authenticated user.",
    responses={
        200: {"description": "User information"},
        401: {"description": "Not authenticated"},
    }
)
async def get_me(
    current_user: User = Depends(get_current_user)
):
    """
    Get current authenticated user's information.
    
    **Requires:** Valid JWT token in Authorization header.
    """
    return UserResponse(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        created_at=current_user.created_at
    )


# ============================================
# VERIFY TOKEN
# ============================================

@router.get(
    "/verify",
    response_model=MessageResponse,
    summary="Verify token",
    description="Check if the current token is valid.",
    responses={
        200: {"description": "Token is valid"},
        401: {"description": "Token is invalid or expired"},
    }
)
async def verify_token(
    current_user: User = Depends(get_current_user)
):
    """
    Verify that the current token is valid.
    
    Useful for checking authentication status on app load.
    """
    return MessageResponse(
        success=True,
        message="Token is valid"
    )