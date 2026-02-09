# ============================================
# PRICEPALLY OPERATIONS TRACKER
# Timezone Utilities
# ============================================

"""
Timezone handling for West Africa Time (WAT).

All timestamps in the application use WAT (Africa/Lagos).
This ensures consistency for Pricepally operations in Nigeria.
"""

from datetime import datetime, date, timedelta
from typing import Optional
import pytz

from app.config import settings


# ============================================
# TIMEZONE SETUP
# ============================================

# West Africa Time timezone
WAT_TIMEZONE = pytz.timezone(settings.timezone)

# UTC timezone for reference
UTC_TIMEZONE = pytz.UTC


# ============================================
# CURRENT TIME FUNCTIONS
# ============================================

def get_wat_timezone() -> pytz.timezone:
    """
    Get the WAT timezone object.
    
    Returns:
        pytz.timezone: West Africa Time timezone
    """
    return WAT_TIMEZONE


def get_current_time() -> datetime:
    """
    Get current time in WAT timezone.
    
    This function is used as the default for all timestamp fields.
    Always returns server time, never client time.
    
    Returns:
        datetime: Current datetime in WAT (Africa/Lagos)
        
    Example:
        >>> get_current_time()
        datetime(2024, 1, 15, 14, 30, 0, tzinfo=<DstTzInfo 'Africa/Lagos' WAT+1:00:00 STD>)
    """
    return datetime.now(WAT_TIMEZONE)


def get_current_date() -> date:
    """
    Get current date in WAT timezone.
    
    Returns:
        date: Current date in WAT
    """
    return get_current_time().date()


# ============================================
# CONVERSION FUNCTIONS
# ============================================

def to_wat(dt: datetime) -> datetime:
    """
    Convert a datetime to WAT timezone.
    
    Args:
        dt: Datetime to convert (can be naive or aware)
        
    Returns:
        datetime: Datetime in WAT timezone
    """
    if dt is None:
        return None
    
    # If naive (no timezone), assume it's in WAT
    if dt.tzinfo is None:
        return WAT_TIMEZONE.localize(dt)
    
    # Convert to WAT
    return dt.astimezone(WAT_TIMEZONE)


def to_utc(dt: datetime) -> datetime:
    """
    Convert a datetime to UTC timezone.
    
    Args:
        dt: Datetime to convert
        
    Returns:
        datetime: Datetime in UTC
    """
    if dt is None:
        return None
    
    # If naive, assume it's in WAT first
    if dt.tzinfo is None:
        dt = WAT_TIMEZONE.localize(dt)
    
    return dt.astimezone(UTC_TIMEZONE)


# ============================================
# FORMATTING FUNCTIONS
# ============================================

def format_datetime(dt: datetime, format_string: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Format a datetime as a string.
    
    Args:
        dt: Datetime to format
        format_string: Format string (default: YYYY-MM-DD HH:MM:SS)
        
    Returns:
        str: Formatted datetime string
        
    Example:
        >>> format_datetime(get_current_time())
        "2024-01-15 14:30:00"
    """
    if dt is None:
        return None
    
    return dt.strftime(format_string)


def format_time_only(dt: datetime) -> str:
    """
    Format only the time portion of a datetime.
    
    Args:
        dt: Datetime to format
        
    Returns:
        str: Time string in HH:MM format
        
    Example:
        >>> format_time_only(get_current_time())
        "14:30"
    """
    if dt is None:
        return None
    
    return dt.strftime("%H:%M")


def format_date_only(dt: datetime) -> str:
    """
    Format only the date portion of a datetime.
    
    Args:
        dt: Datetime to format
        
    Returns:
        str: Date string in YYYY-MM-DD format
    """
    if dt is None:
        return None
    
    return dt.strftime("%Y-%m-%d")


def format_iso(dt: datetime) -> str:
    """
    Format datetime as ISO 8601 string.
    
    Args:
        dt: Datetime to format
        
    Returns:
        str: ISO formatted datetime string
        
    Example:
        >>> format_iso(get_current_time())
        "2024-01-15T14:30:00+01:00"
    """
    if dt is None:
        return None
    
    return dt.isoformat()


# ============================================
# PARSING FUNCTIONS
# ============================================

def parse_date(date_string: str) -> date:
    """
    Parse a date string into a date object.
    
    Args:
        date_string: Date string in YYYY-MM-DD format
        
    Returns:
        date: Parsed date object
        
    Raises:
        ValueError: If date string is invalid
        
    Example:
        >>> parse_date("2024-01-15")
        date(2024, 1, 15)
    """
    return datetime.strptime(date_string, "%Y-%m-%d").date()


def parse_datetime(datetime_string: str) -> datetime:
    """
    Parse a datetime string into a datetime object.
    
    Tries multiple common formats.
    
    Args:
        datetime_string: Datetime string
        
    Returns:
        datetime: Parsed datetime in WAT timezone
        
    Raises:
        ValueError: If datetime string cannot be parsed
    """
    formats = [
        "%Y-%m-%dT%H:%M:%S%z",      # ISO with timezone
        "%Y-%m-%dT%H:%M:%S.%f%z",   # ISO with microseconds and timezone
        "%Y-%m-%dT%H:%M:%S",         # ISO without timezone
        "%Y-%m-%d %H:%M:%S",         # Standard format
        "%Y-%m-%d",                  # Date only
    ]
    
    for fmt in formats:
        try:
            dt = datetime.strptime(datetime_string, fmt)
            return to_wat(dt)
        except ValueError:
            continue
    
    raise ValueError(f"Unable to parse datetime: {datetime_string}")


# ============================================
# DATE COMPARISON FUNCTIONS
# ============================================

def is_past_date(check_date: date) -> bool:
    """
    Check if a date is in the past.
    
    Args:
        check_date: Date to check
        
    Returns:
        bool: True if date is before today
    """
    return check_date < get_current_date()


def is_today(check_date: date) -> bool:
    """
    Check if a date is today.
    
    Args:
        check_date: Date to check
        
    Returns:
        bool: True if date is today
    """
    return check_date == get_current_date()


def is_future_date(check_date: date) -> bool:
    """
    Check if a date is in the future.
    
    Args:
        check_date: Date to check
        
    Returns:
        bool: True if date is after today
    """
    return check_date > get_current_date()


def days_difference(date1: date, date2: date) -> int:
    """
    Calculate the number of days between two dates.
    
    Args:
        date1: First date
        date2: Second date
        
    Returns:
        int: Number of days (positive if date2 > date1)
    """
    return (date2 - date1).days


# ============================================
# DURATION FUNCTIONS
# ============================================

def calculate_duration_minutes(start: datetime, end: datetime) -> int:
    """
    Calculate duration between two datetimes in minutes.
    
    Args:
        start: Start datetime
        end: End datetime
        
    Returns:
        int: Duration in minutes
    """
    if start is None or end is None:
        return 0
    
    delta = end - start
    return int(delta.total_seconds() / 60)


def format_duration(minutes: int) -> str:
    """
    Format duration in minutes as a human-readable string.
    
    Args:
        minutes: Duration in minutes
        
    Returns:
        str: Formatted duration (e.g., "1h 30m", "45m")
        
    Example:
        >>> format_duration(90)
        "1h 30m"
        >>> format_duration(45)
        "45m"
    """
    if minutes is None or minutes < 0:
        return "N/A"
    
    hours = minutes // 60
    mins = minutes % 60
    
    if hours > 0:
        return f"{hours}h {mins}m"
    else:
        return f"{mins}m"