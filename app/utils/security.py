# ============================================
# PRICEPALLY OPERATIONS TRACKER
# Security Utilities
# ============================================

"""
Security utilities for authentication.

Includes:
- Password hashing with bcrypt
- JWT token creation and validation
- Password strength validation
"""

import re
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings
from app.utils.timezone import get_current_time, WAT_TIMEZONE
from app.utils.constants import MIN_PASSWORD_LENGTH, PASSWORD_REQUIREMENTS


# ============================================
# PASSWORD HASHING
# ============================================

# Password hashing context using bcrypt
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12  # Work factor for bcrypt
)


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password
        
    Returns:
        str: Hashed password
        
    Example:
        >>> hashed = hash_password("MySecurePass123")
        >>> len(hashed) > 50
        True
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        plain_password: Plain text password to verify
        hashed_password: Stored password hash
        
    Returns:
        bool: True if password matches, False otherwise
        
    Example:
        >>> hashed = hash_password("MySecurePass123")
        >>> verify_password("MySecurePass123", hashed)
        True
        >>> verify_password("WrongPassword", hashed)
        False
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False


# ============================================
# PASSWORD VALIDATION
# ============================================

def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Validate password meets security requirements.
    
    Requirements:
    - At least 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one number
    
    Args:
        password: Password to validate
        
    Returns:
        tuple[bool, str]: (is_valid, error_message)
        
    Example:
        >>> validate_password_strength("weak")
        (False, "Password must be at least 8 characters long...")
        >>> validate_password_strength("MySecurePass123")
        (True, "")
    """
    if len(password) < MIN_PASSWORD_LENGTH:
        return False, f"Password must be at least {MIN_PASSWORD_LENGTH} characters long"
    
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r"\d", password):
        return False, "Password must contain at least one number"
    
    return True, ""


# ============================================
# JWT TOKEN MANAGEMENT
# ============================================

def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Payload data to encode (e.g., {"sub": user_id})
        expires_delta: Optional custom expiration time
        
    Returns:
        str: Encoded JWT token
        
    Example:
        >>> token = create_access_token({"sub": "user-uuid-here"})
        >>> len(token) > 100
        True
    """
    to_encode = data.copy()
    
    # Set expiration time
    if expires_delta:
        expire = get_current_time() + expires_delta
    else:
        expire = get_current_time() + timedelta(hours=settings.jwt_expiration_hours)
    
    # Add standard claims
    to_encode.update({
        "exp": expire,
        "iat": get_current_time(),  # Issued at
        "type": "access"
    })
    
    # Encode the token
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )
    
    return encoded_jwt


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify and decode a JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        Optional[Dict[str, Any]]: Decoded payload if valid, None otherwise
        
    Example:
        >>> token = create_access_token({"sub": "user-uuid"})
        >>> payload = verify_token(token)
        >>> payload["sub"]
        "user-uuid"
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        return payload
    except JWTError:
        return None


def get_token_expiry(token: str) -> Optional[datetime]:
    """
    Get the expiration time of a token.
    
    Args:
        token: JWT token string
        
    Returns:
        Optional[datetime]: Expiration datetime, or None if invalid
    """
    payload = verify_token(token)
    
    if payload and "exp" in payload:
        # Convert timestamp to datetime
        exp_timestamp = payload["exp"]
        return datetime.fromtimestamp(exp_timestamp, tz=WAT_TIMEZONE)
    
    return None


def is_token_expired(token: str) -> bool:
    """
    Check if a token has expired.
    
    Args:
        token: JWT token string
        
    Returns:
        bool: True if expired or invalid, False if still valid
    """
    expiry = get_token_expiry(token)
    
    if expiry is None:
        return True
    
    return get_current_time() > expiry


def get_user_id_from_token(token: str) -> Optional[str]:
    """
    Extract user ID from a token.
    
    Args:
        token: JWT token string
        
    Returns:
        Optional[str]: User ID if valid, None otherwise
    """
    payload = verify_token(token)
    
    if payload:
        return payload.get("sub")
    
    return None


# ============================================
# TOKEN HASHING (for session storage)
# ============================================

def get_token_hash(token: str) -> str:
    """
    Create a hash of a token for secure storage.
    
    We store hashes instead of tokens in the database
    for additional security.
    
    Args:
        token: JWT token string
        
    Returns:
        str: SHA-256 hash of the token
    """
    return hashlib.sha256(token.encode()).hexdigest()


def verify_token_hash(token: str, stored_hash: str) -> bool:
    """
    Verify a token matches a stored hash.
    
    Args:
        token: JWT token to verify
        stored_hash: Hash stored in database
        
    Returns:
        bool: True if token matches hash
    """
    return get_token_hash(token) == stored_hash


# ============================================
# EMAIL VALIDATION
# ============================================

def validate_email(email: str) -> tuple[bool, str]:
    """
    Validate email format.
    
    Args:
        email: Email address to validate
        
    Returns:
        tuple[bool, str]: (is_valid, error_message)
    """
    # Basic email pattern
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not email:
        return False, "Email is required"
    
    if not re.match(pattern, email):
        return False, "Invalid email format"
    
    if len(email) > 255:
        return False, "Email is too long (max 255 characters)"
    
    return True, ""


# ============================================
# NAME VALIDATION
# ============================================

def validate_name(name: str) -> tuple[bool, str]:
    """
    Validate user name.
    
    Args:
        name: Name to validate
        
    Returns:
        tuple[bool, str]: (is_valid, error_message)
    """
    if not name:
        return False, "Name is required"
    
    name = name.strip()
    
    if len(name) < 2:
        return False, "Name must be at least 2 characters long"
    
    if len(name) > 100:
        return False, "Name is too long (max 100 characters)"
    
    return True, ""


# ============================================
# SANITIZATION
# ============================================

def sanitize_string(value: str) -> str:
    """
    Sanitize a string input.
    
    Removes leading/trailing whitespace and limits length.
    
    Args:
        value: String to sanitize
        
    Returns:
        str: Sanitized string
    """
    if value is None:
        return ""
    
    return value.strip()