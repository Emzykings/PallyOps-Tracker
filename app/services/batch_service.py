# ============================================
# PRICEPALLY OPERATIONS TRACKER
# Batch Service
# ============================================

"""
Batch management business logic.

Handles:
- Listing batches for a date
- Calculating batch status
- Getting batch details with roles
"""

from datetime import date
from typing import List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from app.models.operation import OperationsLog
from app.schemas.batch import (
    BatchStatusResponse,
    BatchListResponse,
    BatchDetailResponse,
    BatchRolesResponse,
)
from app.schemas.operation import RoleStatusResponse
from app.services.operation_service import OperationService
from app.utils.timezone import get_current_date, is_past_date
from app.utils.constants import (
    ROLE_ORDER,
    TOTAL_ROLES,
    RESTRICTED_DAYS,
    BatchStatus,
    OperationStatus,
    get_available_batches_for_date,
    get_day_name,
    get_month_name,
)


class BatchService:
    """
    Service class for batch management.
    """
    
    # ============================================
    # LIST BATCHES FOR DATE
    # ============================================
    
    @staticmethod
    def get_batches_for_date(db: Session, operation_date: date) -> BatchListResponse:
        """
        Get all batches with their status for a date.
        
        Args:
            db: Database session
            operation_date: The operation date
            
        Returns:
            BatchListResponse: List of batches with status
        """
        # Get available batches for this day
        available_batches = get_available_batches_for_date(operation_date)
        
        # Determine if restricted day
        is_restricted = operation_date.isoweekday() in RESTRICTED_DAYS
        
        # Get status for each batch
        batch_statuses = []
        for batch in available_batches:
            status = BatchService._calculate_batch_status(db, operation_date, batch)
            batch_statuses.append(status)
        
        return BatchListResponse(
            success=True,
            operation_date=operation_date,
            day_of_week=get_day_name(operation_date),
            is_restricted_day=is_restricted,
            batches=batch_statuses
        )
    
    # ============================================
    # GET BATCH DETAILS
    # ============================================
    
    @staticmethod
    def get_batch_detail(
        db: Session,
        operation_date: date,
        batch: str
    ) -> Optional[BatchDetailResponse]:
        """
        Get detailed information about a specific batch.
        
        Args:
            db: Database session
            operation_date: The operation date
            batch: Batch identifier
            
        Returns:
            Optional[BatchDetailResponse]: Batch details or None if invalid
        """
        # Validate batch is available for this date
        available_batches = get_available_batches_for_date(operation_date)
        if batch not in available_batches:
            return None
        
        # Calculate status
        status_info = BatchService._calculate_batch_status(db, operation_date, batch)
        
        # Determine if read-only
        is_readonly = is_past_date(operation_date)
        
        return BatchDetailResponse(
            success=True,
            batch=batch,
            operation_date=operation_date,
            day_of_week=get_day_name(operation_date),
            status=status_info.status,
            is_readonly=is_readonly,
            started_count=status_info.started_count,
            completed_count=status_info.completed_count,
            total_roles=status_info.total_roles,
            progress_percentage=status_info.progress_percentage
        )
    
    # ============================================
    # GET BATCH WITH ALL ROLES
    # ============================================
    
    @staticmethod
    def get_batch_with_roles(
        db: Session,
        operation_date: date,
        batch: str
    ) -> Optional[BatchRolesResponse]:
        """
        Get batch details with all role statuses.
        
        Used for the batch workflow page.
        
        Args:
            db: Database session
            operation_date: The operation date
            batch: Batch identifier
            
        Returns:
            Optional[BatchRolesResponse]: Batch with roles or None if invalid
        """
        # Validate batch is available for this date
        available_batches = get_available_batches_for_date(operation_date)
        if batch not in available_batches:
            return None
        
        # Get all roles status
        roles = OperationService.get_all_roles_status(db, operation_date, batch)
        
        # Calculate batch status
        status_info = BatchService._calculate_batch_status(db, operation_date, batch)
        
        # Determine if read-only
        is_readonly = is_past_date(operation_date)
        
        return BatchRolesResponse(
            success=True,
            batch=batch,
            operation_date=operation_date,
            day_of_week=get_day_name(operation_date),
            month=get_month_name(operation_date),
            year=operation_date.year,
            status=status_info.status,
            is_readonly=is_readonly,
            started_count=status_info.started_count,
            completed_count=status_info.completed_count,
            total_roles=status_info.total_roles,
            progress_percentage=status_info.progress_percentage,
            roles=roles
        )
    
    # ============================================
    # BATCH STATUS CALCULATION
    # ============================================
    
    @staticmethod
    def _calculate_batch_status(
        db: Session,
        operation_date: date,
        batch: str
    ) -> BatchStatusResponse:
        """
        Calculate the status of a batch.
        
        Status logic:
        - RED: No roles started
        - YELLOW: Some roles started/in progress
        - GREEN: All roles completed
        
        Args:
            db: Database session
            operation_date: The operation date
            batch: Batch identifier
            
        Returns:
            BatchStatusResponse: Batch status information
        """
        # Count started and completed operations
        started_count = db.query(func.count(OperationsLog.id)).filter(
            and_(
                OperationsLog.operation_date == operation_date,
                OperationsLog.batch == batch,
                OperationsLog.start_time.isnot(None)
            )
        ).scalar() or 0
        
        completed_count = db.query(func.count(OperationsLog.id)).filter(
            and_(
                OperationsLog.operation_date == operation_date,
                OperationsLog.batch == batch,
                OperationsLog.end_time.isnot(None)
            )
        ).scalar() or 0
        
        # Determine status
        if started_count == 0:
            status = BatchStatus.RED
        elif completed_count >= TOTAL_ROLES:
            status = BatchStatus.GREEN
        else:
            status = BatchStatus.YELLOW
        
        # Calculate progress percentage
        progress_percentage = round((completed_count / TOTAL_ROLES) * 100, 2)
        
        return BatchStatusResponse(
            batch=batch,
            status=status,
            started_count=started_count,
            completed_count=completed_count,
            total_roles=TOTAL_ROLES,
            progress_percentage=progress_percentage
        )
    
    # ============================================
    # BATCH VALIDATION
    # ============================================
    
    @staticmethod
    def is_batch_available(operation_date: date, batch: str) -> bool:
        """
        Check if a batch is available for a given date.
        
        Args:
            operation_date: The operation date
            batch: Batch identifier
            
        Returns:
            bool: True if batch is available
        """
        available_batches = get_available_batches_for_date(operation_date)
        return batch in available_batches
    
    # ============================================
    # INITIALIZE BATCH
    # ============================================
    
    @staticmethod
    def initialize_batch(db: Session, operation_date: date, batch: str) -> bool:
        """
        Initialize all role records for a batch.
        
        Creates empty operation records for all 11 roles.
        Useful for pre-populating batch data.
        
        Args:
            db: Database session
            operation_date: The operation date
            batch: Batch identifier
            
        Returns:
            bool: True if successful
        """
        try:
            # Validate batch
            if not BatchService.is_batch_available(operation_date, batch):
                return False
            
            # Create records for each role
            for role in ROLE_ORDER:
                existing = OperationService.get_operation(db, operation_date, batch, role)
                
                if existing is None:
                    operation = OperationsLog(
                        operation_date=operation_date,
                        day_of_week=get_day_name(operation_date),
                        month=get_month_name(operation_date),
                        year=operation_date.year,
                        batch=batch,
                        operation_role=role,
                    )
                    db.add(operation)
            
            db.commit()
            return True
            
        except Exception:
            db.rollback()
            return False
    
    # ============================================
    # DAILY SUMMARY
    # ============================================
    
    @staticmethod
    def get_daily_summary(db: Session, operation_date: date) -> dict:
        """
        Get summary statistics for a day.
        
        Args:
            db: Database session
            operation_date: The operation date
            
        Returns:
            dict: Summary statistics
        """
        available_batches = get_available_batches_for_date(operation_date)
        total_batches = len(available_batches)
        
        # Count completed batches
        completed_batches = 0
        total_completed_roles = 0
        total_orders = 0
        total_on_time = 0
        
        for batch in available_batches:
            status = BatchService._calculate_batch_status(db, operation_date, batch)
            total_completed_roles += status.completed_count
            
            if status.status == BatchStatus.GREEN:
                completed_batches += 1
            
            # Get driver stats
            driver_op = OperationService.get_operation(
                db, operation_date, batch, "Driver"
            )
            if driver_op and driver_op.total_orders:
                total_orders += driver_op.total_orders
                if driver_op.on_time_deliveries:
                    total_on_time += driver_op.on_time_deliveries
        
        total_role_slots = total_batches * TOTAL_ROLES
        overall_progress = round((total_completed_roles / total_role_slots) * 100, 2) if total_role_slots > 0 else 0
        on_time_percentage = round((total_on_time / total_orders) * 100, 2) if total_orders > 0 else None
        
        return {
            "operation_date": operation_date.isoformat(),
            "day_of_week": get_day_name(operation_date),
            "total_batches": total_batches,
            "completed_batches": completed_batches,
            "total_roles": total_role_slots,
            "completed_roles": total_completed_roles,
            "overall_progress": overall_progress,
            "total_orders_delivered": total_orders if total_orders > 0 else None,
            "total_on_time_deliveries": total_on_time if total_on_time > 0 else None,
            "overall_on_time_percentage": on_time_percentage
        }