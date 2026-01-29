"""
Common decorators for route protection and functionality enhancement.

Provides reusable decorators for:
- Rate limiting
- Activity logging
- API key validation
"""
from functools import wraps
from flask import request, g
from tuned.utils.responses import error_response
from tuned.models.audit import ActivityLog
from tuned.redis_client import redis_client
from typing import Callable, Optional
import time


def rate_limit(max_requests: int = 5, window: int = 60, key_prefix: str = 'rate_limit'):
    """
    Rate limiting decorator using Redis.
    
    Args:
        max_requests: Maximum number of requests allowed
        window: Time window in seconds
        key_prefix: Redis key prefix
        
    Example:
        @rate_limit(max_requests=5, window=60)  # 5 requests per minute
        @app.route('/api/endpoint')
        def my_endpoint():
            pass
    """
    def decorator(f: Callable):
        @wraps(f)
        def wrapped(*args, **kwargs):
            # Get client identifier (IP address or user ID)
            if hasattr(g, 'current_user') and g.current_user:
                client_id = f"user:{g.current_user.id}"
            else:
                client_id = f"ip:{request.remote_addr}"
            
            # Create Redis key
            key = f"{key_prefix}:{f.__name__}:{client_id}"
            
            try:
                # Get current request count
                current = redis_client.get(key)
                
                if current is None:
                    # First request in window
                    redis_client.setex(key, window, 1)
                else:
                    current = int(current)
                    
                    if current >= max_requests:
                        return error_response(
                            'Rate limit exceeded. Please try again later.',
                            status=429
                        )
                    
                    # Increment counter
                    redis_client.incr(key)
                
            except Exception as e:
                # If Redis fails, allow request (fail open)
                pass
            
            return f(*args, **kwargs)
        
        return wrapped
    return decorator


def log_activity(action: str, entity_type: Optional[str] = None):
    """
    Decorator to automatically log activity to ActivityLog.
    
    Args:
        action: Action name (e.g., 'user_login', 'order_created')
        entity_type: Optional entity type (e.g., 'User', 'Order')
        
    Example:
        @log_activity('user_profile_updated', 'User')
        @jwt_required()
        def update_profile():
            # Activity is logged automatically
            pass
    """
    def decorator(f: Callable):
        @wraps(f)
        def wrapped(*args, **kwargs):
            # Execute the function
            result = f(*args, **kwargs)
            
            # Log activity after successful execution
            try:
                user_id = None
                if hasattr(g, 'current_user') and g.current_user:
                    user_id = g.current_user.id
                
                # Extract entity_id from result if it's a tuple (response, status_code)
                entity_id = None
                if isinstance(result, tuple) and len(result) == 2:
                    response_data = result[0].get_json() if hasattr(result[0], 'get_json') else None
                    if response_data and 'data' in response_data:
                        if isinstance(response_data['data'], dict) and 'id' in response_data['data']:
                            entity_id = response_data['data']['id']
                
                ActivityLog.log(
                    action=action,
                    user_id=user_id,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent')
                )
            except Exception as e:
                # Don't fail the request if logging fails
                import logging
                logging.error(f"Failed to log activity: {str(e)}")
            
            return result
        
        return wrapped
    return decorator


def require_api_key(f: Callable):
    """
    Decorator to require API key authentication.
    
    API key should be provided in header: X-API-Key
    
    Example:
        @require_api_key
        @app.route('/api/internal/endpoint')
        def internal_endpoint():
            pass
    """
    @wraps(f)
    def wrapped(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        
        if not api_key:
            return error_response('API key is required', status=401)
        
        # Get expected API key from config
        from flask import current_app
        expected_key = current_app.config.get('API_KEY')
        
        if not expected_key or api_key != expected_key:
            return error_response('Invalid API key', status=403)
        
        return f(*args, **kwargs)
    
    return wrapped


def cors_preflight(allowed_methods: list = None):
    """
    Decorator to handle CORS preflight requests.
    
    Args:
        allowed_methods: List of allowed HTTP methods
        
    Example:
        @cors_preflight(['GET', 'POST'])
        @app.route('/api/endpoint', methods=['GET', 'POST', 'OPTIONS'])
        def endpoint():
            pass
    """
    if allowed_methods is None:
        allowed_methods = ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
    
    def decorator(f: Callable):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if request.method == 'OPTIONS':
                from flask import make_response
                response = make_response('', 204)
                response.headers['Access-Control-Allow-Methods'] = ', '.join(allowed_methods)
                response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
                response.headers['Access-Control-Max-Age'] = '3600'
                return response
            
            return f(*args, **kwargs)
        
        return wrapped
    return decorator
