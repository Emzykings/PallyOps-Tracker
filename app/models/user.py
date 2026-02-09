# ============================================
# PRICEPALLY OPERATIONS TRACKER
# User Model
# ============================================

"""
User-related database models.

Tables:
- users: Stores user account information
- user_sessions: Tracks active JWT sessions
"""

import uuid
from datetime import datetime
from sqlalchemy import (
    Column,
    String,
    DateTime,
    ForeignKey,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base
from app.utils.timezone import get_current_time


class User(Base):
    """
    User model for authentication.
    
    All users have equal access - no admin roles.
    
    Attributes:
        id: Unique identifier (UUID)
        name: User's display name
        email: Unique email address
        password_hash: Bcrypt hashed password
        created_at: Account creation timestamp
    """
    
    __tablename__ = "users"
    
    # --- Primary Key ---
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique user identifier"
    )
    
    # --- User Information ---
    name = Column(
        String(100),
        nullable=False,
        comment="User display name"
    )
    
    email = Column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
        comment="User email address (unique)"
    )
    
    password_hash = Column(
        String(255),
        nullable=False,
        comment="Bcrypt hashed password"
    )
    
    # --- Timestamps ---
    created_at = Column(
        DateTime(timezone=True),
        default=get_current_time,
        nullable=False,
        comment="Account creation timestamp"
    )
    
    # --- Relationships ---
    sessions = relationship(
        "UserSession",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    # Operations started by this user
    operations_started = relationship(
        "OperationsLog",
        foreign_keys="OperationsLog.started_by_user_id",
        back_populates="started_by_user"
    )
    
    # Operations completed by this user
    operations_completed = relationship(
        "OperationsLog",
        foreign_keys="OperationsLog.completed_by_user_id",
        back_populates="completed_by_user"
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, name='{self.name}', email='{self.email}')>"
    
    def to_dict(self) -> dict:
        """Convert user to dictionary (excluding sensitive data)."""
        return {
            "id": str(self.id),
            "name": self.name,
            "email": self.email,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class UserSession(Base):
    """
    User session model for JWT tracking.
    
    Enables token invalidation on logout.
    
    Attributes:
        id: Unique session identifier
        user_id: Reference to user
        token_hash: Hash of JWT token
        expires_at: Token expiration time
        created_at: Session creation timestamp
    """
    
    __tablename__ = "user_sessions"
    
    # --- Primary Key ---
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique session identifier"
    )
    
    # --- Foreign Key ---
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Reference to user"
    )
    
    # --- Session Data ---
    token_hash = Column(
        String(255),
        nullable=False,
        comment="Hash of JWT token for validation"
    )
    
    expires_at = Column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        comment="Token expiration timestamp"
    )
    
    created_at = Column(
        DateTime(timezone=True),
        default=get_current_time,
        nullable=False,
        comment="Session creation timestamp"
    )
    
    # --- Relationships ---
    user = relationship("User", back_populates="sessions")
    
    def __repr__(self) -> str:
        return f"<UserSession(id={self.id}, user_id={self.user_id})>"
    
    def is_expired(self) -> bool:
        """Check if session has expired."""
        return datetime.now(self.expires_at.tzinfo) > self.expires_at


# --- Indexes ---
Index("idx_users_email", User.email)
Index("idx_sessions_user", UserSession.user_id)
Index("idx_sessions_expiry", UserSession.expires_at)