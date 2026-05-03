from functools import wraps
from flask import request, g
from tuned.redis_client import redis_client
from typing import Callable, Any, Optional
import logging

logger = logging.getLogger(__name__)

def rate_limit(max_requests: int = 5, window: int = 60, key_prefix: str = 'rate_limit') -> Callable[..., Any]:
    def decorator(f: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(f)
        def wrapped(*args: Any, **kwargs: Any) -> Any:
            if hasattr(g, 'current_user') and g.current_user:
                client_id = f"user:{g.current_user.id}"
            else:
                client_id = f"ip:{request.remote_addr}"
            
            key = f"{key_prefix}:{f.__name__}:{client_id}"
            
            try:
                current: Optional[Any] = redis_client.get(key)
                if current is None:
                    redis_client.setex(key, window, 1)
                else:
                    current_val: int = int(current)
                    if current_val >= max_requests:
                        from tuned.utils.responses import error_response
                        return error_response('Rate limit exceeded. Please try again later.', status=429)
                    redis_client.incr(key)
            except Exception:
                pass
            
            return f(*args, **kwargs)
        return wrapped
    return decorator