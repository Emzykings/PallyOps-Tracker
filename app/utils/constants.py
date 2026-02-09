# ============================================
# PRICEPALLY OPERATIONS TRACKER
# Application Constants
# ============================================

"""
Central location for all application constants.

This ensures consistency across the application
and makes updates easy to manage.
"""

from datetime import date
from typing import List, Optional


# ============================================
# FULFILLMENT ROLES
# ============================================

# Ordered list of all fulfillment roles
# This order is the RECOMMENDED workflow sequence
ROLE_ORDER: List[str] = [
    "Procurement",
    "Inventory QC - IN",
    "QC - Preppers",
    "Pre-stagers",
    "Extra Service Preppers",
    "Pickers and Packers",
    "QC-out",
    "Stock handler 1",
    "Stock handler 2",
    "Manifester",
    "Driver",
]

# Set for quick validation
VALID_ROLES: set = set(ROLE_ORDER)

# Total number of roles
TOTAL_ROLES: int = len(ROLE_ORDER)

# Role that requires special handling (delivery stats)
DRIVER_ROLE: str = "Driver"


# ============================================
# BATCHES
# ============================================

# All possible batches
ALL_BATCHES: List[str] = ["A", "B", "C", "D"]

# Batches for Monday and Thursday (no D)
RESTRICTED_BATCHES: List[str] = ["A", "B", "C"]

# Set for quick validation
VALID_BATCHES: set = set(ALL_BATCHES)

# Days with restricted batches (0=Monday, 3=Thursday in Python)
# Using isoweekday: 1=Monday, 4=Thursday
RESTRICTED_DAYS: set = {1, 4}  # Monday and Thursday


# ============================================
# STATUS VALUES
# ============================================

class OperationStatus:
    """Operation status constants."""
    
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"


class BatchStatus:
    """Batch status constants (for color coding)."""
    
    RED = "RED"        # No roles started
    YELLOW = "YELLOW"  # Some roles in progress
    GREEN = "GREEN"    # All roles completed


# ============================================
# PASSWORD VALIDATION
# ============================================

# Minimum password length
MIN_PASSWORD_LENGTH: int = 8

# Password requirements message
PASSWORD_REQUIREMENTS: str = (
    "Password must be at least 8 characters long and contain "
    "at least one uppercase letter, one lowercase letter, and one number."
)


# ============================================
# HELPER FUNCTIONS
# ============================================

def get_role_index(role: str) -> int:
    """
    Get the index (order position) of a role.
    
    Args:
        role: Role name
        
    Returns:
        int: Index position (0-based), or -1 if not found
    """
    try:
        return ROLE_ORDER.index(role)
    except ValueError:
        return -1


def get_previous_role(role: str) -> Optional[str]:
    """
    Get the previous role in the workflow sequence.
    
    Args:
        role: Current role name
        
    Returns:
        Optional[str]: Previous role name, or None if first role
        
    Example:
        >>> get_previous_role("QC - Preppers")
        "Inventory QC - IN"
        >>> get_previous_role("Procurement")
        None
    """
    index = get_role_index(role)
    
    if index <= 0:
        return None
    
    return ROLE_ORDER[index - 1]


def get_next_role(role: str) -> Optional[str]:
    """
    Get the next role in the workflow sequence.
    
    Args:
        role: Current role name
        
    Returns:
        Optional[str]: Next role name, or None if last role
        
    Example:
        >>> get_next_role("Procurement")
        "Inventory QC - IN"
        >>> get_next_role("Driver")
        None
    """
    index = get_role_index(role)
    
    if index < 0 or index >= len(ROLE_ORDER) - 1:
        return None
    
    return ROLE_ORDER[index + 1]


def get_available_batches_for_date(operation_date: date) -> List[str]:
    """
    Get available batches for a given date.
    
    Monday and Thursday have only batches A, B, C.
    Other days have batches A, B, C, D.
    
    Args:
        operation_date: The operation date
        
    Returns:
        List[str]: List of available batch identifiers
        
    Example:
        >>> from datetime import date
        >>> get_available_batches_for_date(date(2024, 1, 15))  # Monday
        ['A', 'B', 'C']
        >>> get_available_batches_for_date(date(2024, 1, 17))  # Wednesday
        ['A', 'B', 'C', 'D']
    """
    # isoweekday: 1=Monday, 2=Tuesday, ..., 7=Sunday
    day_of_week = operation_date.isoweekday()
    
    if day_of_week in RESTRICTED_DAYS:
        return RESTRICTED_BATCHES.copy()
    
    return ALL_BATCHES.copy()


def is_valid_role(role: str) -> bool:
    """
    Check if a role name is valid.
    
    Args:
        role: Role name to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    return role in VALID_ROLES


def is_valid_batch(batch: str) -> bool:
    """
    Check if a batch identifier is valid.
    
    Args:
        batch: Batch identifier to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    return batch in VALID_BATCHES


def is_driver_role(role: str) -> bool:
    """
    Check if a role is the Driver role.
    
    Args:
        role: Role name
        
    Returns:
        bool: True if Driver role, False otherwise
    """
    return role == DRIVER_ROLE


def get_day_name(operation_date: date) -> str:
    """
    Get the day name for a date.
    
    Args:
        operation_date: The date
        
    Returns:
        str: Day name (Monday, Tuesday, etc.)
    """
    return operation_date.strftime("%A")


def get_month_name(operation_date: date) -> str:
    """
    Get the month name for a date.
    
    Args:
        operation_date: The date
        
    Returns:
        str: Month name (January, February, etc.)
    """
    return operation_date.strftime("%B")


# ============================================
# API RESPONSE MESSAGES
# ============================================

class Messages:
    """Standard API response messages."""
    
    # Success messages
    REGISTRATION_SUCCESS = "User registered successfully"
    LOGIN_SUCCESS = "Login successful"
    LOGOUT_SUCCESS = "Logged out successfully"
    OPERATION_STARTED = "Operation started successfully"
    OPERATION_COMPLETED = "Operation completed successfully"
    
    # Error messages
    INVALID_CREDENTIALS = "Invalid email or password"
    EMAIL_EXISTS = "Email already registered"
    USER_NOT_FOUND = "User not found"
    INVALID_TOKEN = "Invalid or expired token"
    TOKEN_EXPIRED = "Token has expired"
    
    # Operation errors
    OPERATION_ALREADY_STARTED = "Operation already started"
    OPERATION_NOT_STARTED = "Operation has not been started yet"
    OPERATION_ALREADY_COMPLETED = "Operation already completed"
    INVALID_ROLE = "Invalid role name"
    INVALID_BATCH = "Invalid batch identifier"
    BATCH_NOT_AVAILABLE = "Batch not available for this date"
    READONLY_DATE = "Cannot modify operations for past dates"
    
    # Warnings
    PREVIOUS_NOT_COMPLETED = "Previous operation not completed yet"
    ROLES_NOT_COMPLETED = "Some roles are not yet completed"
    
    # Driver-specific
    DRIVER_ORDERS_REQUIRED = "Total orders is required for Driver role"
    INVALID_ORDERS_COUNT = "On-time deliveries cannot exceed total orders"