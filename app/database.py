# ============================================
# PRICEPALLY OPERATIONS TRACKER
# Database Connection & Session Management
# ============================================

"""
SQLAlchemy database configuration.
Handles connection pooling and session lifecycle.
"""

from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from app.config import settings


# ============================================
# DATABASE ENGINE
# ============================================

# Create SQLAlchemy engine with connection pooling
engine = create_engine(
    settings.database_url,
    
    # Connection pool settings for production stability
    pool_size=5,           # Number of connections to keep open
    max_overflow=10,       # Additional connections when pool is full
    pool_timeout=30,       # Seconds to wait for available connection
    pool_recycle=1800,     # Recycle connections after 30 minutes
    pool_pre_ping=True,    # Verify connection is alive before using
    
    # Echo SQL statements in debug mode
    echo=settings.debug,
)


# ============================================
# SESSION FACTORY
# ============================================

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,      # Require explicit commits
    autoflush=False,       # Don't auto-flush before queries
    bind=engine,
)


# ============================================
# BASE MODEL CLASS
# ============================================

# Base class for all SQLAlchemy models
Base = declarative_base()


# ============================================
# DEPENDENCY INJECTION
# ============================================

def get_db() -> Generator[Session, None, None]:
    """
    Database session dependency for FastAPI.
    
    Creates a new database session for each request,
    and ensures it's closed after the request completes.
    
    Usage in FastAPI:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    
    Yields:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================
# DATABASE INITIALIZATION
# ============================================

def init_db() -> None:
    """
    Initialize database tables.
    
    Creates all tables defined in models if they don't exist.
    Called on application startup.
    """
    # Import all models to register them with Base
    from app.models import user, operation  # noqa: F401
    
    # Create all tables
    Base.metadata.create_all(bind=engine)


def check_db_connection() -> bool:
    """
    Check if database connection is working.
    
    Returns:
        bool: True if connection successful, False otherwise
    """
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))  # ✅ Fixed - using text()
        db.close()
        return True
    except Exception as e:
        print(f"Database connection error: {e}")
        return False