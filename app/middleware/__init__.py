# ============================================
# PRICEPALLY OPERATIONS TRACKER
# Middleware Package Initialization
# ============================================

"""
Middleware and dependencies for request processing.

This package contains:
- auth_middleware: JWT authentication dependency
- error_handlers: Global error handling
- cors_middleware: CORS and security headers
"""

from app.middleware.auth_middleware import (
    get_current_user,
    get_current_user_optional,
    oauth2_scheme,
    rate_limit_dependency,
    RequestContext,
)
from app.middleware.error_handlers import (
    register_error_handlers,
    register_custom_exception_handlers,
    AppException,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ConflictError,
    OperationError,
)
from app.middleware.cors_middleware import (
    configure_cors,
    configure_security_middleware,
    configure_logging_middleware,
)

__all__ = [
    # Auth middleware
    "get_current_user",
    "get_current_user_optional",
    "oauth2_scheme",
    "rate_limit_dependency",
    "RequestContext",
    # Error handlers
    "register_error_handlers",
    "register_custom_exception_handlers",
    "AppException",
    "AuthenticationError",
    "AuthorizationError",
    "NotFoundError",
    "ConflictError",
    "OperationError",
    # CORS & Security
    "configure_cors",
    "configure_security_middleware",
    "configure_logging_middleware",
]