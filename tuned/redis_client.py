import redis
from typing import Any, cast
from redis import Redis
from tuned.core.config import config
import os

def get_redis_client() -> Redis:
    config_name = os.environ.get('FLASK_ENV', 'development')
    flask_config = config[config_name]
    
    redis_client: Redis = redis.from_url(  # type: ignore[no-untyped-call]
        flask_config.REDIS_URL,
        decode_responses=True
    )
    
    return redis_client

redis_client = get_redis_client()

def add_token_to_blacklist(jti: str, expires_in: int) -> None:
    redis_client.setex(
        f"blacklist:{jti}",
        expires_in,
        "true"
    )

def is_token_blacklisted(jti: str) -> bool:
    return bool(cast(Any, redis_client.exists(f"blacklist:{jti}")) > 0)
