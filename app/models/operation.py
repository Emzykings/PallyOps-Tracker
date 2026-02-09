# ============================================
# PRICEPALLY OPERATIONS TRACKER
# Operations Log Model
# ============================================

"""
Operations logging database model.

This is the core table that tracks timing for each role
across batches and operation dates.
"""

import uuid
from sqlalchemy import (
    Column,
    String,
    Integer,
    Date,
    DateTime,
    ForeignKey,
    Index,
    CheckConstraint,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base
from app.utils.timezone import get_current_time
from app.utils.constants import VALID_BATCHES, VALID_ROLES


class OperationsLog(Base):
    """
    Operations timing log.
    
    Tracks start/end times for each role in each batch.
    One record per (operation_date, batch, role) combination.
    
    Attributes:
        id: Unique record identifier
        operation_date: Date of the fulfillment operation
        day_of_week: Day name (Monday, Tuesday, etc.)
        month: Month name (January, February, etc.)
        year: Year (2024, 2025, etc.)
        batch: Batch identifier (A, B, C, D)
        operation_role: Role name
        start_time: When role started (server timestamp)
        end_time: When role completed (server timestamp)
        total_orders: Driver only - total orders delivered
        on_time_deliveries: Driver only - orders delivered on time
        started_by_user_id: User who clicked START
        completed_by_user_id: User who clicked DONE
        created_at: Record creation timestamp
        updated_at: Last update timestamp
    """
    
    __tablename__ = "operations_log"
    
    # --- Primary Key ---
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique record identifier"
    )
    
    # --- Date Information ---
    operation_date = Column(
        Date,
        nullable=False,
        index=True,
        comment="Fulfillment operation date"
    )
    
    day_of_week = Column(
        String(10),
        nullable=False,
        comment="Day name (Monday, Tuesday, etc.)"
    )
    
    month = Column(
        String(10),
        nullable=False,
        comment="Month name (January, February, etc.)"
    )
    
    year = Column(
        Integer,
        nullable=False,
        comment="Year (2024, 2025, etc.)"
    )
    
    # --- Batch & Role ---
    batch = Column(
        String(1),
        nullable=False,
        index=True,
        comment="Batch identifier (A, B, C, D)"
    )
    
    operation_role = Column(
        String(50),
        nullable=False,
        index=True,
        comment="Role name"
    )
    
    # --- Timing (Immutable once set) ---
    start_time = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Role start timestamp (server time)"
    )
    
    end_time = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Role completion timestamp (server time)"
    )
    
    # --- Driver-specific Fields ---
    total_orders = Column(
        Integer,
        nullable=True,
        comment="Driver: Total orders delivered"
    )
    
    on_time_deliveries = Column(
        Integer,
        nullable=True,
        comment="Driver: Orders delivered before deadline"
    )
    
    # --- User References ---
    started_by_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
        comment="User who started this role"
    )
    
    completed_by_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
        comment="User who completed this role"
    )
    
    # --- Timestamps ---
    created_at = Column(
        DateTime(timezone=True),
        default=get_current_time,
        nullable=False,
        comment="Record creation timestamp"
    )
    
    updated_at = Column(
        DateTime(timezone=True),
        default=get_current_time,
        onupdate=get_current_time,
        nullable=False,
        comment="Last update timestamp"
    )
    
    # --- Relationships ---
    started_by_user = relationship(
        "User",
        foreign_keys=[started_by_user_id],
        back_populates="operations_started"
    )
    
    completed_by_user = relationship(
        "User",
        foreign_keys=[completed_by_user_id],
        back_populates="operations_completed"
    )
    
    # --- Table Constraints ---
    __table_args__ = (
        # Unique constraint: One record per date/batch/role
        UniqueConstraint(
            "operation_date",
            "batch",
            "operation_role",
            name="unique_operation"
        ),
        
        # Batch must be valid
        CheckConstraint(
            f"batch IN {tuple(VALID_BATCHES)}",
            name="valid_batch"
        ),
        
        # Role must be valid
        CheckConstraint(
            f"operation_role IN {tuple(VALID_ROLES)}",
            name="valid_role"
        ),
        
        # End time must be after start time
        CheckConstraint(
            "end_time IS NULL OR end_time >= start_time",
            name="end_after_start"
        ),
        
        # Year must be reasonable
        CheckConstraint(
            "year >= 2024 AND year <= 2100",
            name="valid_year"
        ),
        
        # Driver must have orders if completed
        CheckConstraint(
            "(operation_role != 'Driver') OR (end_time IS NULL) OR (total_orders IS NOT NULL AND total_orders >= 0)",
            name="driver_orders_valid"
        ),
        
        # On-time cannot exceed total
        CheckConstraint(
            "on_time_deliveries IS NULL OR total_orders IS NULL OR on_time_deliveries <= total_orders",
            name="on_time_not_exceed_total"
        ),
        
        # Indexes
        Index("idx_operations_date_batch", "operation_date", "batch"),
        Index("idx_operations_composite", "operation_date", "batch", "operation_role"),
    )
    
    def __repr__(self) -> str:
        return (
            f"<OperationsLog("
            f"date={self.operation_date}, "
            f"batch={self.batch}, "
            f"role='{self.operation_role}', "
            f"status={self.status}"
            f")>"
        )
    
    @property
    def status(self) -> str:
        """
        Calculate current status of this operation.
        
        Returns:
            str: 'PENDING', 'IN_PROGRESS', or 'COMPLETED'
        """
        if self.end_time is not None:
            return "COMPLETED"
        elif self.start_time is not None:
            return "IN_PROGRESS"
        else:
            return "PENDING"
    
    @property
    def duration_minutes(self) -> int | None:
        """
        Calculate duration in minutes.
        
        Returns:
            int | None: Duration in minutes, or None if not completed
        """
        if self.start_time and self.end_time:
            delta = self.end_time - self.start_time
            return int(delta.total_seconds() / 60)
        return None
    
    @property
    def on_time_percentage(self) -> float | None:
        """
        Calculate on-time delivery percentage (Driver only).
        
        Returns:
            float | None: Percentage, or None if not applicable
        """
        if self.total_orders and self.total_orders > 0 and self.on_time_deliveries is not None:
            return round((self.on_time_deliveries / self.total_orders) * 100, 2)
        return None
    
    def to_dict(self) -> dict:
        """Convert operation to dictionary."""
        return {
            "id": str(self.id),
            "operation_date": self.operation_date.isoformat() if self.operation_date else None,
            "day_of_week": self.day_of_week,
            "month": self.month,
            "year": self.year,
            "batch": self.batch,
            "operation_role": self.operation_role,
            "status": self.status,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_minutes": self.duration_minutes,
            "total_orders": self.total_orders,
            "on_time_deliveries": self.on_time_deliveries,
            "on_time_percentage": self.on_time_percentage,
            "started_by": self.started_by_user.name if self.started_by_user else None,
            "completed_by": self.completed_by_user.name if self.completed_by_user else None,
        }