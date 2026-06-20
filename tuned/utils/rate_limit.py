from __future__ import annotations

from tuned.redis_client import redis_client


def socket_rate_limit(key: str, limit: int, window: int) -> bool:
    """
    Redis sliding-window rate limiter for socket events.

    Args:
        key:    Unique key (e.g. f"socket:mark_read:{user_id}")
        limit:  Max calls allowed within `window` seconds
        window: Time window in seconds

    Returns:
        True if the call is allowed, False if rate-limited.
    """
    try:
        pipe = redis_client.pipeline()
        pipe.incr(key)
        pipe.expire(key, window)
        count, _ = pipe.execute()
        return int(count) <= limit
    except Exception:
        # Graceful fallback: allow connection if Redis is down
        return True
