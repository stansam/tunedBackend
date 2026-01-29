"""
Token generation and validation utilities using itsdangerous.

Provides secure, stateless token generation for:
- Email verification
- Password reset
- Other time-sensitive operations

All tokens are cryptographically signed and include expiration.
"""
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from flask import current_app
from typing import Optional, Dict, Any
import secrets
import string


def get_serializer() -> URLSafeTimedSerializer:
    """
    Get the token serializer instance.
    
    Returns:
        URLSafeTimedSerializer: Configured serializer
    """
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'])


def generate_token(data: Dict[str, Any], salt: str) -> str:
    """
    Generate a secure, signed token with embedded data.
    
    Args:
        data: Dictionary of data to embed in token
        salt: Salt for token generation (use different salts for different purposes)
        
    Returns:
        str: Signed token string
        
    Example:
        token = generate_token({'user_id': 123}, 'email-verification')
    """
    serializer = get_serializer()
    return serializer.dumps(data, salt=salt)


def verify_token(token: str, salt: str, max_age: int = 3600) -> Optional[Dict[str, Any]]:
    """
    Verify and decode a token.
    
    Args:
        token: Token string to verify
        salt: Salt used during token generation
        max_age: Maximum age of token in seconds (default: 1 hour)
        
    Returns:
        Dict or None: Token data if valid, None if invalid/expired
        
    Example:
        data = verify_token(token, 'email-verification', max_age=86400)
        if data:
            user_id = data['user_id']
    """
    serializer = get_serializer()
    
    try:
        data = serializer.loads(token, salt=salt, max_age=max_age)
        return data
    except (SignatureExpired, BadSignature):
        return None


def generate_verification_token(user_id: int, email: str) -> str:
    """
    Generate an email verification token.
    
    Args:
        user_id: User ID
        email: User email address
        
    Returns:
        str: Verification token (valid for 24 hours)
        
    Example:
        token = generate_verification_token(user.id, user.email)
    """
    return generate_token(
        {'user_id': user_id, 'email': email},
        salt='email-verification'
    )


def verify_verification_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify an email verification token.
    
    Args:
        token: Verification token
        
    Returns:
        Dict or None: {'user_id': int, 'email': str} if valid, None otherwise
        
    Example:
        data = verify_verification_token(token)
        if data:
            user_id = data['user_id']
            email = data['email']
    """
    # 24 hours = 86400 seconds
    return verify_token(token, salt='email-verification', max_age=86400)


def generate_password_reset_token(user_id: int, email: str) -> str:
    """
    Generate a password reset token.
    
    Args:
        user_id: User ID
        email: User email address
        
    Returns:
        str: Reset token (valid for 1 hour)
        
    Example:
        token = generate_password_reset_token(user.id, user.email)
    """
    return generate_token(
        {'user_id': user_id, 'email': email},
        salt='password-reset'
    )


def verify_password_reset_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify a password reset token.
    
    Args:
        token: Reset token
        
    Returns:
        Dict or None: {'user_id': int, 'email': str} if valid, None otherwise
        
    Example:
        data = verify_password_reset_token(token)
        if data:
            user_id = data['user_id']
    """
    # 1 hour = 3600 seconds
    return verify_token(token, salt='password-reset', max_age=3600)


def generate_referral_code(length: int = 8) -> str:
    """
    Generate a unique referral code.
    
    Args:
        length: Length of the code (default: 8)
        
    Returns:
        str: Random alphanumeric code
        
    Example:
        code = generate_referral_code()  # Returns something like "K7X9M2P4"
    """
    # Use uppercase letters and digits only (exclude ambiguous characters)
    chars = string.ascii_uppercase + string.digits
    chars = chars.replace('0', '').replace('O', '').replace('I', '').replace('1')
    
    return ''.join(secrets.choice(chars) for _ in range(length))


def generate_secure_random_string(length: int = 32) -> str:
    """
    Generate a cryptographically secure random string.
    
    Args:
        length: Length of the string
        
    Returns:
        str: Random hex string
        
    Example:
        api_key = generate_secure_random_string(32)
    """
    return secrets.token_hex(length // 2)
