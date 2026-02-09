# ============================================
# PRICEPALLY OPERATIONS TRACKER
# Operation Service
# ============================================

"""
Operation timing business logic.

Handles:
- Starting operations
- Completing operations
- Driver-specific completion
- Checking previous role status
- Concurrent access control
"""

from datetime import date
from typing import Optional, Tuple, Dict, Any
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_

from app.models.operation import OperationsLog
from app.models.user import User
from app.schemas.operation import (
    OperationStart,
    OperationEnd,
    DriverEnd,
    OperationResponse,
    OperationStartResponse,
    OperationEndResponse,
    RoleStatusResponse,
    PreviousRoleCheck,
    AlreadyStartedResponse,
)
from app.utils.timezone import get_current_time, is_past_date
from app.utils.constants import (
    ROLE_ORDER,
    TOTAL_ROLES,
    DRIVER_ROLE,
    OperationStatus,
    Messages,
    get_previous_role,
    get_role_index,
    get_day_name,
    get_month_name,
    get_available_batches_for_date,
)


class OperationService:
    """
    Service class for operation timing management.
    """
    
    # ============================================
    # START OPERATION
    # ============================================
    
    @staticmethod
    def start_operation(
        db: Session,
        data: OperationStart,
        user: User
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Start an operation (record start time).
        
        Args:
            db: Database session
            data: Operation start data
            user: User performing the action
            
        Returns:
            Tuple containing:
                - success: bool
                - message: str
                - response_data: dict with operation data and optional warning
        """
        try:
            # Validate batch is available for this date
            available_batches = get_available_batches_for_date(data.operation_date)
            if data.batch not in available_batches:
                return False, Messages.BATCH_NOT_AVAILABLE, None
            
            # Check if date is in the past (read-only)
            if is_past_date(data.operation_date):
                return False, Messages.READONLY_DATE, None
            
            # Get or create operation record
            operation = OperationService._get_or_create_operation(
                db=db,
                operation_date=data.operation_date,
                batch=data.batch,
                role=data.role
            )
            
            # Check if already started
            if operation.start_time is not None:
                started_by_name = operation.started_by_user.name if operation.started_by_user else "Unknown"
                return False, Messages.OPERATION_ALREADY_STARTED, {
                    "error": "ALREADY_STARTED",
                    "started_by": started_by_name,
                    "started_at": operation.start_time.isoformat()
                }
            
            # Check previous role status for warning
            warning = None
            previous_role = get_previous_role(data.role)
            if previous_role:
                prev_operation = OperationService.get_operation(
                    db=db,
                    operation_date=data.operation_date,
                    batch=data.batch,
                    role=previous_role
                )
                if prev_operation and prev_operation.end_time is None:
                    warning = f"Previous operation '{previous_role}' not completed yet"
            
            # Record start time (SERVER TIMESTAMP)
            operation.start_time = get_current_time()
            operation.started_by_user_id = user.id
            
            db.commit()
            db.refresh(operation)
            
            # Build response
            response_data = {
                "operation": OperationService._to_response(operation),
                "warning": warning
            }
            
            return True, Messages.OPERATION_STARTED, response_data
            
        except IntegrityError:
            db.rollback()
            return False, Messages.OPERATION_ALREADY_STARTED, None
        except Exception as e:
            db.rollback()
            return False, f"Failed to start operation: {str(e)}", None
    
    # ============================================
    # END OPERATION (Non-Driver)
    # ============================================
    
    @staticmethod
    def end_operation(
        db: Session,
        data: OperationEnd,
        user: User
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Complete an operation (record end time).
        
        Args:
            db: Database session
            data: Operation end data
            user: User performing the action
            
        Returns:
            Tuple containing:
                - success: bool
                - message: str
                - response_data: dict with operation data
        """
        try:
            # Check if date is in the past (read-only)
            if is_past_date(data.operation_date):
                return False, Messages.READONLY_DATE, None
            
            # Get operation record
            operation = OperationService.get_operation(
                db=db,
                operation_date=data.operation_date,
                batch=data.batch,
                role=data.role
            )
            
            if not operation:
                return False, Messages.OPERATION_NOT_STARTED, None
            
            # Check if already completed
            if operation.end_time is not None:
                return False, Messages.OPERATION_ALREADY_COMPLETED, None
            
            # Check if started
            if operation.start_time is None:
                return False, Messages.OPERATION_NOT_STARTED, None
            
            # Record end time (SERVER TIMESTAMP)
            operation.end_time = get_current_time()
            operation.completed_by_user_id = user.id
            
            db.commit()
            db.refresh(operation)
            
            # Build response
            response_data = {
                "operation": OperationService._to_response(operation),
                "warning": None
            }
            
            return True, Messages.OPERATION_COMPLETED, response_data
            
        except Exception as e:
            db.rollback()
            return False, f"Failed to complete operation: {str(e)}", None
    
    # ============================================
    # END DRIVER OPERATION
    # ============================================
    
    @staticmethod
    def end_driver_operation(
        db: Session,
        data: DriverEnd,
        user: User
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Complete Driver operation with delivery statistics.
        
        Args:
            db: Database session
            data: Driver completion data
            user: User performing the action
            
        Returns:
            Tuple containing:
                - success: bool
                - message: str
                - response_data: dict with operation data and optional warning
        """
        try:
            # Check if date is in the past (read-only)
            if is_past_date(data.operation_date):
                return False, Messages.READONLY_DATE, None
            
            # Get Driver operation record
            operation = OperationService.get_operation(
                db=db,
                operation_date=data.operation_date,
                batch=data.batch,
                role=DRIVER_ROLE
            )
            
            if not operation:
                return False, Messages.OPERATION_NOT_STARTED, None
            
            # Check if already completed
            if operation.end_time is not None:
                return False, Messages.OPERATION_ALREADY_COMPLETED, None
            
            # Check if started
            if operation.start_time is None:
                return False, Messages.OPERATION_NOT_STARTED, None
            
            # Check if other roles are incomplete (for warning)
            warning = None
            incomplete_roles = OperationService._get_incomplete_roles(
                db=db,
                operation_date=data.operation_date,
                batch=data.batch,
                exclude_role=DRIVER_ROLE
            )
            if incomplete_roles:
                warning = f"Roles not completed: {', '.join(incomplete_roles)}"
            
            # Record end time and delivery stats (SERVER TIMESTAMP)
            operation.end_time = get_current_time()
            operation.completed_by_user_id = user.id
            operation.total_orders = data.total_orders
            operation.on_time_deliveries = data.on_time_deliveries
            
            db.commit()
            db.refresh(operation)
            
            # Build response
            response_data = {
                "operation": OperationService._to_response(operation),
                "warning": warning
            }
            
            return True, Messages.OPERATION_COMPLETED, response_data
            
        except Exception as e:
            db.rollback()
            return False, f"Failed to complete driver operation: {str(e)}", None
    
    # ============================================
    # CHECK PREVIOUS ROLE
    # ============================================
    
    @staticmethod
    def check_previous_role(
        db: Session,
        operation_date: date,
        batch: str,
        role: str
    ) -> PreviousRoleCheck:
        """
        Check if the previous role in sequence is completed.
        
        Used to show warning when starting out of order.
        
        Args:
            db: Database session
            operation_date: Operation date
            batch: Batch identifier
            role: Current role
            
        Returns:
            PreviousRoleCheck: Check result with warning info
        """
        previous_role = get_previous_role(role)
        
        # First role has no previous
        if previous_role is None:
            return PreviousRoleCheck(
                current_role=role,
                previous_role=None,
                is_previous_completed=True,
                show_warning=False,
                warning_message=None
            )
        
        # Check previous role status
        prev_operation = OperationService.get_operation(
            db=db,
            operation_date=operation_date,
            batch=batch,
            role=previous_role
        )
        
        is_completed = prev_operation is not None and prev_operation.end_time is not None
        show_warning = not is_completed
        
        warning_message = None
        if show_warning:
            warning_message = f"Previous operation '{previous_role}' not completed yet. Continue anyway?"
        
        return PreviousRoleCheck(
            current_role=role,
            previous_role=previous_role,
            is_previous_completed=is_completed,
            show_warning=show_warning,
            warning_message=warning_message
        )
    
    # ============================================
    # GET OPERATIONS
    # ============================================
    
    @staticmethod
    def get_operation(
        db: Session,
        operation_date: date,
        batch: str,
        role: str
    ) -> Optional[OperationsLog]:
        """
        Get a specific operation record.
        
        Args:
            db: Database session
            operation_date: Operation date
            batch: Batch identifier
            role: Role name
            
        Returns:
            Optional[OperationsLog]: Operation record or None
        """
        return db.query(OperationsLog).filter(
            and_(
                OperationsLog.operation_date == operation_date,
                OperationsLog.batch == batch,
                OperationsLog.operation_role == role
            )
        ).first()
    
    @staticmethod
    def get_batch_operations(
        db: Session,
        operation_date: date,
        batch: str
    ) -> list[OperationsLog]:
        """
        Get all operations for a batch.
        
        Args:
            db: Database session
            operation_date: Operation date
            batch: Batch identifier
            
        Returns:
            list[OperationsLog]: List of operation records
        """
        return db.query(OperationsLog).filter(
            and_(
                OperationsLog.operation_date == operation_date,
                OperationsLog.batch == batch
            )
        ).all()
    
    # ============================================
    # ROLE STATUS LIST
    # ============================================
    
    @staticmethod
    def get_all_roles_status(
        db: Session,
        operation_date: date,
        batch: str
    ) -> list[RoleStatusResponse]:
        """
        Get status of all roles for a batch.
        
        Returns roles in workflow order with their current status.
        
        Args:
            db: Database session
            operation_date: Operation date
            batch: Batch identifier
            
        Returns:
            list[RoleStatusResponse]: List of role statuses in order
        """
        # Get existing operations for this batch
        operations = OperationService.get_batch_operations(db, operation_date, batch)
        
        # Create a map for quick lookup
        op_map = {op.operation_role: op for op in operations}
        
        # Build status list for all roles
        roles_status = []
        for index, role in enumerate(ROLE_ORDER):
            operation = op_map.get(role)
            
            if operation:
                status = operation.status
                roles_status.append(RoleStatusResponse(
                    role=role,
                    order=index + 1,
                    status=status,
                    start_time=operation.start_time,
                    end_time=operation.end_time,
                    duration_minutes=operation.duration_minutes,
                    started_by=operation.started_by_user.name if operation.started_by_user else None,
                    completed_by=operation.completed_by_user.name if operation.completed_by_user else None,
                    total_orders=operation.total_orders,
                    on_time_deliveries=operation.on_time_deliveries,
                    on_time_percentage=operation.on_time_percentage,
                ))
            else:
                # Role not yet created - PENDING
                roles_status.append(RoleStatusResponse(
                    role=role,
                    order=index + 1,
                    status=OperationStatus.PENDING,
                    start_time=None,
                    end_time=None,
                    duration_minutes=None,
                    started_by=None,
                    completed_by=None,
                    total_orders=None,
                    on_time_deliveries=None,
                    on_time_percentage=None,
                ))
        
        return roles_status
    
    # ============================================
    # HELPER METHODS
    # ============================================
    
    @staticmethod
    def _get_or_create_operation(
        db: Session,
        operation_date: date,
        batch: str,
        role: str
    ) -> OperationsLog:
        """
        Get existing operation or create new one.
        
        Args:
            db: Database session
            operation_date: Operation date
            batch: Batch identifier
            role: Role name
            
        Returns:
            OperationsLog: Existing or new operation record
        """
        operation = OperationService.get_operation(db, operation_date, batch, role)
        
        if operation is None:
            operation = OperationsLog(
                operation_date=operation_date,
                day_of_week=get_day_name(operation_date),
                month=get_month_name(operation_date),
                year=operation_date.year,
                batch=batch,
                operation_role=role,
            )
            db.add(operation)
            db.flush()  # Get ID without committing
        
        return operation
    
    @staticmethod
    def _get_incomplete_roles(
        db: Session,
        operation_date: date,
        batch: str,
        exclude_role: str = None
    ) -> list[str]:
        """
        Get list of roles that are not completed.
        
        Args:
            db: Database session
            operation_date: Operation date
            batch: Batch identifier
            exclude_role: Role to exclude from check
            
        Returns:
            list[str]: List of incomplete role names
        """
        incomplete = []
        
        for role in ROLE_ORDER:
            if role == exclude_role:
                continue
            
            operation = OperationService.get_operation(db, operation_date, batch, role)
            
            if operation is None or operation.end_time is None:
                incomplete.append(role)
        
        return incomplete
    
    @staticmethod
    def _to_response(operation: OperationsLog) -> dict:
        """
        Convert operation to response dictionary.
        
        Args:
            operation: Operation record
            
        Returns:
            dict: Operation data
        """
        return {
            "id": str(operation.id),
            "operation_date": operation.operation_date.isoformat(),
            "day_of_week": operation.day_of_week,
            "month": operation.month,
            "year": operation.year,
            "batch": operation.batch,
            "operation_role": operation.operation_role,
            "status": operation.status,
            "start_time": operation.start_time.isoformat() if operation.start_time else None,
            "end_time": operation.end_time.isoformat() if operation.end_time else None,
            "duration_minutes": operation.duration_minutes,
            "total_orders": operation.total_orders,
            "on_time_deliveries": operation.on_time_deliveries,
            "on_time_percentage": operation.on_time_percentage,
            "started_by": operation.started_by_user.name if operation.started_by_user else None,
            "completed_by": operation.completed_by_user.name if operation.completed_by_user else None,
        }