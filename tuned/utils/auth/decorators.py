from functools import wraps
from flask import g
from flask_login import current_user
from tuned.models.user import User
from tuned.utils.responses import error_response, unauthorized_response, forbidden_response
from typing import Callable, Any


def admin_required(f: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(f)
    def wrapped(*args: Any, **kwargs: Any) -> Any:
        user = User.query.get(str(current_user.id))
        
        if not user:
            return unauthorized_response('User not found')
        
        if not user.is_admin:
            return forbidden_response('Admin privileges required')
        
        g.current_user = user
        
        return f(*args, **kwargs)
    
    return wrapped


def verified_email_required(f: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(f)
    def wrapped(*args: Any, **kwargs: Any) -> Any:
        user = User.query.get(str(current_user.id))
        
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


def active_user_required(f: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(f)
    def wrapped(*args: Any, **kwargs: Any) -> Any:
        user = User.query.get(str(current_user.id))
        
        if not user:
            return unauthorized_response('User not found')
        
        if not user.is_active or user.deleted_at:
            return forbidden_response('Account is deactivated')
        
        g.current_user = user
        
        return f(*args, **kwargs)
    
    return wrapped


def combined_auth_check(require_verified: bool = True, require_admin: bool = False) -> Callable[..., Any]:
    def decorator(f: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(f)
        def wrapped(*args: Any, **kwargs: Any) -> Any:
            user = User.query.get(str(current_user.id))
            
            if not user:
                return unauthorized_response('User not found')
            
            if not user.is_active or user.deleted_at:
                return forbidden_response('Account is deactivated')
            
            if require_verified and not user.email_verified:
                return error_response(
                    'Email verification required',
                    status=403
                )
            
            if require_admin and not user.is_admin:
                return forbidden_response('Admin privileges required')
            
            g.current_user = user
            
            return f(*args, **kwargs)
        
        return wrapped
    return decorator
