# ============================================
# PRICEPALLY OPERATIONS TRACKER
# Authentication Service
# ============================================

"""
Authentication business logic.

Handles:
- User registration
- User login
- Token management
- Session tracking
"""

from datetime import timedelta
from typing import Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.user import User, UserSession
from app.schemas.user import UserCreate, UserLogin, UserResponse, TokenResponse, AuthResponse
from app.utils.security import (
    hash_password,
    verify_password,
    create_access_token,
    get_token_hash,
    validate_password_strength,
    validate_email,
    validate_name,
)
from app.utils.timezone import get_current_time
from app.utils.constants import Messages
from app.config import settings


class AuthService:
    """
    Service class for authentication operations.
    
    All methods are static for easy use without instantiation.
    """
    
    # ============================================
    # USER REGISTRATION
    # ============================================
    
    @staticmethod
    def register_user(db: Session, user_data: UserCreate) -> Tuple[bool, str, Optional[AuthResponse]]:
        """
        Register a new user.
        
        Args:
            db: Database session
            user_data: User registration data
            
        Returns:
            Tuple[bool, str, Optional[AuthResponse]]: 
                - success: Whether registration was successful
                - message: Success or error message
                - response: Auth response with user and token (if successful)
        """
        try:
            # Check if email already exists
            existing_user = db.query(User).filter(User.email == user_data.email.lower()).first()
            if existing_user:
                return False, Messages.EMAIL_EXISTS, None
            
            # Create new user
            new_user = User(
                name=user_data.name.strip(),
                email=user_data.email.lower().strip(),
                password_hash=hash_password(user_data.password),
            )
            
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            
            # Generate token
            token = AuthService._create_user_token(db, new_user)
            
            # Build response
            response = AuthService._build_auth_response(
                user=new_user,
                token=token,
                message=Messages.REGISTRATION_SUCCESS
            )
            
            return True, Messages.REGISTRATION_SUCCESS, response
            
        except IntegrityError:
            db.rollback()
            return False, Messages.EMAIL_EXISTS, None
        except Exception as e:
            db.rollback()
            return False, f"Registration failed: {str(e)}", None
    
    # ============================================
    # USER LOGIN
    # ============================================
    
    @staticmethod
    def login_user(db: Session, login_data: UserLogin) -> Tuple[bool, str, Optional[AuthResponse]]:
        """
        Authenticate a user and return token.
        
        Args:
            db: Database session
            login_data: Login credentials
            
        Returns:
            Tuple[bool, str, Optional[AuthResponse]]:
                - success: Whether login was successful
                - message: Success or error message
                - response: Auth response with user and token (if successful)
        """
        try:
            # Find user by email
            user = db.query(User).filter(User.email == login_data.email.lower()).first()
            
            if not user:
                return False, Messages.INVALID_CREDENTIALS, None
            
            # Verify password
            if not verify_password(login_data.password, user.password_hash):
                return False, Messages.INVALID_CREDENTIALS, None
            
            # Generate token
            token = AuthService._create_user_token(db, user)
            
            # Build response
            response = AuthService._build_auth_response(
                user=user,
                token=token,
                message=Messages.LOGIN_SUCCESS
            )
            
            return True, Messages.LOGIN_SUCCESS, response
            
        except Exception as e:
            return False, f"Login failed: {str(e)}", None
    
    # ============================================
    # USER LOGOUT
    # ============================================
    
    @staticmethod
    def logout_user(db: Session, token: str, user_id: UUID) -> Tuple[bool, str]:
        """
        Logout user by invalidating their session.
        
        Args:
            db: Database session
            token: JWT token to invalidate
            user_id: User's ID
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            # Find and delete the session
            token_hash = get_token_hash(token)
            session = db.query(UserSession).filter(
                UserSession.user_id == user_id,
                UserSession.token_hash == token_hash
            ).first()
            
            if session:
                db.delete(session)
                db.commit()
            
            return True, Messages.LOGOUT_SUCCESS
            
        except Exception as e:
            db.rollback()
            return False, f"Logout failed: {str(e)}"
    
    # ============================================
    # USER RETRIEVAL
    # ============================================
    
    @staticmethod
    def get_user_by_id(db: Session, user_id: UUID) -> Optional[User]:
        """
        Get user by ID.
        
        Args:
            db: Database session
            user_id: User's UUID
            
        Returns:
            Optional[User]: User object or None if not found
        """
        return db.query(User).filter(User.id == user_id).first()
    
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """
        Get user by email.
        
        Args:
            db: Database session
            email: User's email
            
        Returns:
            Optional[User]: User object or None if not found
        """
        return db.query(User).filter(User.email == email.lower()).first()
    
    # ============================================
    # SESSION VALIDATION
    # ============================================
    
    @staticmethod
    def validate_session(db: Session, token: str, user_id: UUID) -> bool:
        """
        Validate that a token session is still active.
        
        Args:
            db: Database session
            token: JWT token
            user_id: User's ID
            
        Returns:
            bool: True if session is valid and not expired
        """
        try:
            token_hash = get_token_hash(token)
            session = db.query(UserSession).filter(
                UserSession.user_id == user_id,
                UserSession.token_hash == token_hash
            ).first()
            
            if not session:
                return False
            
            # Check if expired
            if session.expires_at < get_current_time():
                # Clean up expired session
                db.delete(session)
                db.commit()
                return False
            
            return True
            
        except Exception:
            return False
    
    # ============================================
    # SESSION CLEANUP
    # ============================================
    
    @staticmethod
    def cleanup_expired_sessions(db: Session) -> int:
        """
        Remove all expired sessions from database.
        
        Args:
            db: Database session
            
        Returns:
            int: Number of sessions removed
        """
        try:
            current_time = get_current_time()
            result = db.query(UserSession).filter(
                UserSession.expires_at < current_time
            ).delete()
            db.commit()
            return result
        except Exception:
            db.rollback()
            return 0
    
    # ============================================
    # HELPER METHODS
    # ============================================
    
    @staticmethod
    def _create_user_token(db: Session, user: User) -> str:
        """
        Create JWT token and store session.
        
        Args:
            db: Database session
            user: User object
            
        Returns:
            str: JWT token
        """
        # Create token with user ID
        token = create_access_token(
            data={"sub": str(user.id)},
            expires_delta=timedelta(hours=settings.jwt_expiration_hours)
        )
        
        # Store session in database
        session = UserSession(
            user_id=user.id,
            token_hash=get_token_hash(token),
            expires_at=get_current_time() + timedelta(hours=settings.jwt_expiration_hours)
        )
        
        db.add(session)
        db.commit()
        
        return token
    
    @staticmethod
    def _build_auth_response(user: User, token: str, message: str) -> AuthResponse:
        """
        Build authentication response object.
        
        Args:
            user: User object
            token: JWT token
            message: Response message
            
        Returns:
            AuthResponse: Complete auth response
        """
        user_response = UserResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            created_at=user.created_at
        )
        
        token_response = TokenResponse(
            access_token=token,
            token_type="bearer",
            expires_in=settings.jwt_expiration_hours * 3600  # Convert to seconds
        )
        
        return AuthResponse(
            success=True,
            message=message,
            user=user_response,
            token=token_response
        )