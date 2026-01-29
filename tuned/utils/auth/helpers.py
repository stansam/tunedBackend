"""
Auth-specific helper functions.

Provides common authentication-related helper functions:
- Current user retrieval
- Login attempt tracking
- Account lockout checking
- IP extraction
"""
from flask import request, g
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from tuned.models.user import User
from tuned.extensions import db
from datetime import datetime, timezone, timedelta
from typing import Optional
import logging


logger = logging.getLogger(__name__)


def get_current_user() -> Optional[User]:
    """
    Get the currently authenticated user from JWT token.
    
    Returns:
        User or None: User object if authenticated, None otherwise
        
    Example:
        user = get_current_user()
        if user:
            # User is authenticated
            pass
    """
    try:
        # Verify JWT is present
        verify_jwt_in_request(optional=True)
        
        # Get user ID from JWT
        user_id = get_jwt_identity()
        
        if user_id:
            # Retrieve user from database
            user = User.query.get(int(user_id))
            
            # Store in g for request context
            g.current_user = user
            
            return user
        
        return None
        
    except Exception as e:
        logger.debug(f"Failed to get current user: {str(e)}")
        return None


def check_account_lockout(user: User) -> tuple[bool, Optional[str]]:
    """
    Check if user account is locked out due to failed login attempts.
    
    Lockout policy:
    - 5 failed attempts triggers lockout
    - Lockout duration: 15 minutes
    
    Args:
        user: User model instance
        
    Returns:
        tuple: (is_locked, lock_expires_message)
        
    Example:
        locked, message = check_account_lockout(user)
        if locked:
            return error_response(message, status=403)
    """
    # Check if user has failed login attempts
    if user.failed_login_attempts >= 5:
        # Check if lockout period has expired
        if user.last_failed_login:
            lockout_duration = timedelta(minutes=15)
            lockout_expires = user.last_failed_login + lockout_duration
            
            if datetime.now(timezone.utc) < lockout_expires:
                # Still locked out
                remaining = lockout_expires - datetime.now(timezone.utc)
                minutes = int(remaining.total_seconds() / 60)
                
                return True, f"Account temporarily locked. Try again in {minutes} minutes."
            else:
                # Lockout expired, reset counter
                user.failed_login_attempts = 0
                user.last_failed_login = None
                db.session.commit()
                return False, None
    
    return False, None


def record_login_attempt(user: User, success: bool = True, ip_address: Optional[str] = None) -> None:
    """
    Record a login attempt (successful or failed).
    
    Args:
        user: User model instance
        success: True if login was successful, False if failed
        ip_address: Optional IP address of the attempt
        
    Example:
        if verify_password(password, user.password_hash):
            record_login_attempt(user, success=True, ip_address=request.remote_addr)
        else:
            record_login_attempt(user, success=False, ip_address=request.remote_addr)
    """
    if success:
        # Reset failed attempts on successful login
        user.failed_login_attempts = 0
        user.last_failed_login = None
        user.last_login_at = datetime.now(timezone.utc)
        
        logger.info(f"Successful login for user {user.id} from IP {ip_address}")
        
    else:
        # Increment failed attempts
        user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
        user.last_failed_login = datetime.now(timezone.utc)
        
        logger.warning(
            f"Failed login attempt for user {user.id} from IP {ip_address}. "
            f"Total attempts: {user.failed_login_attempts}"
        )
    
    db.session.commit()


def get_user_ip() -> str:
    """
    Extract the real IP address from request headers.
    
    Handles proxy forwarding (X-Forwarded-For, X-Real-IP).
    
    Returns:
        str: Client IP address
        
    Example:
        ip = get_user_ip()
        ActivityLog.log(action='login', ip_address=ip)
    """
    # Check for proxied IP addresses
    if request.headers.get('X-Forwarded-For'):
        # X-Forwarded-For can contain multiple IPs, use the first (client)
        ip = request.headers.get('X-Forwarded-For').split(',')[0].strip()
    elif request.headers.get('X-Real-IP'):
        ip = request.headers.get('X-Real-IP')
    else:
        ip = request.remote_addr
    
    return ip or 'unknown'


def get_user_agent() -> str:
    """
    Get the User-Agent header from request.
    
    Returns:
        str: User agent string
    """
    return request.headers.get('User-Agent', 'unknown')


def is_email_verified_required() -> bool:
    """
    Check if email verification is required for login.
    
    This checks the application configuration.
    
    Returns:
        bool: True if email verification is required
    """
    from flask import current_app
    return current_app.config.get('REQUIRE_EMAIL_VERIFICATION', True)


def get_user_by_email_or_username(identifier: str) -> Optional[User]:
    """
    Get user by email or username.
    
    Args:
        identifier: Email address or username
        
    Returns:
        User or None: User if found, None otherwise
        
    Example:
        user = get_user_by_email_or_username(login_input)
    """
    # Try email first (most common)
    user = User.query.filter_by(email=identifier).first()
    
    if not user:
        # Try username
        user = User.query.filter_by(username=identifier).first()
    
    return user
