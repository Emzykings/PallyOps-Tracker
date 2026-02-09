# ============================================
# PRICEPALLY OPERATIONS TRACKER
# Authentication Middleware
# ============================================

"""
JWT authentication middleware and dependencies.

Provides:
- Token extraction from requests
- Token validation
- User retrieval from token
- Protected route dependency
"""

from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.services.auth_service import AuthService
from app.utils.security import verify_token, get_user_id_from_token
from app.utils.constants import Messages


# ============================================
# OAUTH2 SCHEME
# ============================================

# OAuth2 scheme for token extraction from Authorization header
# tokenUrl is the endpoint where clients can obtain tokens
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    auto_error=True  # Automatically return 401 if no token
)

# Optional version that doesn't error if no token present
oauth2_scheme_optional = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    auto_error=False  # Don't error, just return None
)


# ============================================
# AUTHENTICATION DEPENDENCIES
# ============================================

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to get the current authenticated user.
    
    Extracts and validates JWT token from Authorization header,
    then retrieves the user from database.
    
    Usage:
        @app.get("/protected")
        def protected_route(current_user: User = Depends(get_current_user)):
            return {"user": current_user.name}
    
    Args:
        token: JWT token from Authorization header
        db: Database session
        
    Returns:
        User: Authenticated user object
        
    Raises:
        HTTPException: 401 if token is invalid or user not found
    """
    # Define the credentials exception
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=Messages.INVALID_TOKEN,
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Verify token and extract payload
    payload = verify_token(token)
    if payload is None:
        raise credentials_exception
    
    # Extract user ID from token
    user_id_str: str = payload.get("sub")
    if user_id_str is None:
        raise credentials_exception
    
    try:
        user_id = UUID(user_id_str)
    except ValueError:
        raise credentials_exception
    
    # Get user from database
    user = AuthService.get_user_by_id(db, user_id)
    if user is None:
        raise credentials_exception
    
    # Optionally validate session is still active
    # (Uncomment if you want strict session tracking)
    # if not AuthService.validate_session(db, token, user_id):
    #     raise credentials_exception
    
    return user


async def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme_optional),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Dependency to optionally get the current user.
    
    Unlike get_current_user, this doesn't raise an error
    if no token is present. Returns None instead.
    
    Useful for routes that work differently for authenticated
    vs unauthenticated users.
    
    Usage:
        @app.get("/public")
        def public_route(current_user: Optional[User] = Depends(get_current_user_optional)):
            if current_user:
                return {"message": f"Hello, {current_user.name}"}
            return {"message": "Hello, guest"}
    
    Args:
        token: Optional JWT token from Authorization header
        db: Database session
        
    Returns:
        Optional[User]: User object if authenticated, None otherwise
    """
    if token is None:
        return None
    
    try:
        # Verify token and extract payload
        payload = verify_token(token)
        if payload is None:
            return None
        
        # Extract user ID from token
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            return None
        
        user_id = UUID(user_id_str)
        
        # Get user from database
        user = AuthService.get_user_by_id(db, user_id)
        return user
        
    except Exception:
        return None


# ============================================
# TOKEN EXTRACTION HELPERS
# ============================================

def extract_token_from_header(authorization: str) -> Optional[str]:
    """
    Extract token from Authorization header.
    
    Args:
        authorization: Full Authorization header value
        
    Returns:
        Optional[str]: Token string or None
        
    Example:
        >>> extract_token_from_header("Bearer eyJhbGc...")
        "eyJhbGc..."
    """
    if not authorization:
        return None
    
    parts = authorization.split()
    
    if len(parts) != 2:
        return None
    
    scheme, token = parts
    
    if scheme.lower() != "bearer":
        return None
    
    return token


# ============================================
# PERMISSION HELPERS
# ============================================

def require_authenticated(user: Optional[User]) -> User:
    """
    Helper to ensure user is authenticated.
    
    Use in routes where authentication is conditionally required.
    
    Args:
        user: User object or None
        
    Returns:
        User: Authenticated user
        
    Raises:
        HTTPException: 401 if user is None
    """
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=Messages.INVALID_TOKEN,
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


# ============================================
# RATE LIMITING (Basic Implementation)
# ============================================

# Note: For production, consider using a proper rate limiting library
# like slowapi or implementing Redis-based rate limiting

from collections import defaultdict
from datetime import datetime, timedelta
from threading import Lock

# Simple in-memory rate limiter
_rate_limit_store: dict = defaultdict(list)
_rate_limit_lock = Lock()


def check_rate_limit(
    identifier: str,
    max_requests: int = 60,
    window_seconds: int = 60
) -> bool:
    """
    Check if request is within rate limit.
    
    Simple in-memory implementation. For production,
    use Redis or similar distributed cache.
    
    Args:
        identifier: Unique identifier (e.g., user ID or IP)
        max_requests: Maximum requests allowed in window
        window_seconds: Time window in seconds
        
    Returns:
        bool: True if within limit, False if exceeded
    """
    now = datetime.now()
    window_start = now - timedelta(seconds=window_seconds)
    
    with _rate_limit_lock:
        # Get request timestamps for this identifier
        requests = _rate_limit_store[identifier]
        
        # Remove old requests outside the window
        requests = [ts for ts in requests if ts > window_start]
        _rate_limit_store[identifier] = requests
        
        # Check if within limit
        if len(requests) >= max_requests:
            return False
        
        # Add current request
        requests.append(now)
        _rate_limit_store[identifier] = requests
        
        return True


async def rate_limit_dependency(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency that applies rate limiting per user.
    
    Args:
        current_user: Authenticated user
        
    Returns:
        User: The authenticated user
        
    Raises:
        HTTPException: 429 if rate limit exceeded
    """
    from app.config import settings
    
    if not check_rate_limit(
        identifier=str(current_user.id),
        max_requests=settings.rate_limit_per_minute,
        window_seconds=60
    ):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later."
        )
    
    return current_user


# ============================================
# REQUEST CONTEXT
# ============================================

class RequestContext:
    """
    Context object for passing request information.
    
    Useful for logging and auditing.
    """
    
    def __init__(
        self,
        user: Optional[User] = None,
        token: Optional[str] = None,
        request_id: Optional[str] = None
    ):
        self.user = user
        self.token = token
        self.request_id = request_id
        self.timestamp = datetime.now()
    
    @property
    def user_id(self) -> Optional[UUID]:
        return self.user.id if self.user else None
    
    @property
    def user_name(self) -> Optional[str]:
        return self.user.name if self.user else None
    
    def to_dict(self) -> dict:
        return {
            "user_id": str(self.user_id) if self.user_id else None,
            "user_name": self.user_name,
            "request_id": self.request_id,
            "timestamp": self.timestamp.isoformat()
        }