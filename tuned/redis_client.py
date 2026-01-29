"""
Redis client configuration for JWT blacklist and caching.

This module provides a configured Redis client instance used for:
- JWT token blacklisting (logout functionality)
- Session storage (optional)
- Caching (future use)
"""
import redis
from tuned.config import config
import os


def get_redis_client():
    """
    Create and return a configured Redis client.
    
    Returns:
        redis.Redis: Configured Redis client instance
    """
    # Get config name from environment
    config_name = os.environ.get('FLASK_ENV', 'development')
    flask_config = config[config_name]
    
    # Create Redis client
    redis_client = redis.from_url(
        flask_config.REDIS_URL,
        decode_responses=True  # Automatically decode bytes to strings
    )
    
    return redis_client


# Create Redis client instance
redis_client = get_redis_client()


def add_token_to_blacklist(jti, expires_in):
    """
    Add a JWT token identifier to the blacklist.
    
    Args:
        jti (str): JWT ID (unique identifier for the token)
        expires_in (int): Seconds until token expires
    """
    redis_client.setex(
        f"blacklist:{jti}",
        expires_in,
        "true"
    )


def is_token_blacklisted(jti):
    """
    Check if a JWT token is blacklisted.
    
    Args:
        jti (str): JWT ID to check
        
    Returns:
        bool: True if token is blacklisted, False otherwise
    """
    return redis_client.exists(f"blacklist:{jti}") > 0
