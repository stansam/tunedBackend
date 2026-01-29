"""
Auth-specific decorators for route protection.

Provides decorators for:
- JWT token verification with freshness
- Admin role requirement
- Email verification requirement
- Active user requirement
"""
from functools import wraps
from flask import g
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity, get_jwt
from tuned.models.user import User
from tuned.utils.responses import error_response, unauthorized_response, forbidden_response
from typing import Callable


def jwt_required_fresh(f: Callable):
    """
    Require a fresh JWT token (recently authenticated).
    
    Use this for sensitive operations like password changes.
    
    Example:
        @jwt_required_fresh
        @app.route('/api/change-password')
        def change_password():
            pass
    """
    @wraps(f)
    def wrapped(*args, **kwargs):
        # Verify JWT and check freshness
        verify_jwt_in_request(fresh=True)
        
        user_id = get_jwt_identity()
        user = User.query.get(int(user_id))
        
        if not user:
            return unauthorized_response('User not found')
        
        g.current_user = user
        
        return f(*args, **kwargs)
    
    return wrapped


def admin_required(f: Callable):
    """
    Require user to have admin privileges.
    
    Must be used after @jwt_required() or similar decorator.
    
    Example:
        from flask_jwt_extended import jwt_required
        
        @jwt_required()
        @admin_required
        @app.route('/api/admin/users')
        def manage_users():
            pass
    """
    @wraps(f)
    def wrapped(*args, **kwargs):
        # Get current user from JWT
        user_id = get_jwt_identity()
        user = User.query.get(int(user_id))
        
        if not user:
            return unauthorized_response('User not found')
        
        if not user.is_admin:
            return forbidden_response('Admin privileges required')
        
        g.current_user = user
        
        return f(*args, **kwargs)
    
    return wrapped


def verified_email_required(f: Callable):
    """
    Require user to have verified email address.
    
    Must be used after @jwt_required() or similar decorator.
    
    Example:
        from flask_jwt_extended import jwt_required
        
        @jwt_required()
        @verified_email_required
        @app.route('/api/orders')
        def create_order():
            pass
    """
    @wraps(f)
    def wrapped(*args, **kwargs):
        # Get current user from JWT
        user_id = get_jwt_identity()
        user = User.query.get(int(user_id))
        
        if not user:
            return unauthorized_response('User not found')
        
        if not user.email_verified:
            return error_response(
                'Email verification required. Please check your email for the verification link.',
                status=403
            )
        
        g.current_user = user
        
        return f(*args, **kwargs)
    
    return wrapped


def active_user_required(f: Callable):
    """
    Require user account to be active (not soft-deleted).
    
    Must be used after @jwt_required() or similar decorator.
    
    Example:
        from flask_jwt_extended import jwt_required
        
        @jwt_required()
        @active_user_required
        @app.route('/api/profile')
        def get_profile():
            pass
    """
    @wraps(f)
    def wrapped(*args, **kwargs):
        # Get current user from JWT
        user_id = get_jwt_identity()
        user = User.query.get(int(user_id))
        
        if not user:
            return unauthorized_response('User not found')
        
        if not user.is_active or user.deleted_at:
            return forbidden_response('Account is deactivated')
        
        g.current_user = user
        
        return f(*args, **kwargs)
    
    return wrapped


def combined_auth_check(require_verified: bool = True, require_admin: bool = False):
    """
    Combined auth decorator with configurable checks.
    
    Verifies JWT and checks user status in one decorator.
    
    Args:
        require_verified: Require email verification
        require_admin: Require admin privileges
        
    Example:
        @combined_auth_check(require_verified=True, require_admin=False)
        @app.route('/api/dashboard')
        def dashboard():
            # User is authenticated, active, and email verified
            pass
    """
    def decorator(f: Callable):
        @wraps(f)
        def wrapped(*args, **kwargs):
            # Verify JWT
            verify_jwt_in_request()
            
            user_id = get_jwt_identity()
            user = User.query.get(int(user_id))
            
            if not user:
                return unauthorized_response('User not found')
            
            # Check if active
            if not user.is_active or user.deleted_at:
                return forbidden_response('Account is deactivated')
            
            # Check email verification if required
            if require_verified and not user.email_verified:
                return error_response(
                    'Email verification required',
                    status=403
                )
            
            # Check admin if required
            if require_admin and not user.is_admin:
                return forbidden_response('Admin privileges required')
            
            g.current_user = user
            
            return f(*args, **kwargs)
        
        return wrapped
    return decorator
