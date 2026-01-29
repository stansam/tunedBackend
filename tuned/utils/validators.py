"""
Common validation utilities.

Provides reusable validation functions for common data types
to ensure data integrity and security across the application.
"""
import re
from typing import Optional
import html


def validate_email(email: str) -> bool:
    """
    Validate email address format.
    
    Args:
        email: Email address to validate
        
    Returns:
        bool: True if valid, False otherwise
        
    Example:
        if not validate_email(user_email):
            raise ValidationError('Invalid email format')
    """
    if not email or not isinstance(email, str):
        return False
    
    # RFC 5322 compliant email regex (simplified)
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    # Additional checks
    if len(email) > 320:  # RFC 5321 max length
        return False
    
    if '..' in email:  # No consecutive dots
        return False
        
    return bool(re.match(pattern, email.strip()))


def validate_password_strength(password: str) -> tuple[bool, Optional[str]]:
    """
    Validate password strength against security policy.
    
    Password requirements:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    
    Args:
        password: Password to validate
        
    Returns:
        tuple: (is_valid, error_message)
        
    Example:
        valid, error = validate_password_strength(password)
        if not valid:
            return error_response(error)
    """
    if not password or not isinstance(password, str):
        return False, 'Password is required'
    
    if len(password) < 8:
        return False, 'Password must be at least 8 characters long'
    
    if len(password) > 128:
        return False, 'Password must not exceed 128 characters'
    
    if not re.search(r'[A-Z]', password):
        return False, 'Password must contain at least one uppercase letter'
    
    if not re.search(r'[a-z]', password):
        return False, 'Password must contain at least one lowercase letter'
    
    if not re.search(r'\d', password):
        return False, 'Password must contain at least one digit'
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\\/;]', password):
        return False, 'Password must contain at least one special character'
    
    # Check for common weak passwords
    common_passwords = ['password', '12345678', 'password123', 'qwerty123']
    if password.lower() in common_passwords:
        return False, 'Password is too common, please choose a stronger password'
    
    return True, None


def validate_phone_number(phone: str) -> bool:
    """
    Validate phone number format (international format).
    
    Accepts formats like:
    - +1234567890
    - +1 (234) 567-8900
    - +1-234-567-8900
    
    Args:
        phone: Phone number to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not phone or not isinstance(phone, str):
        return False
    
    # Remove all spaces, dashes, and parentheses
    cleaned = re.sub(r'[\s\-\(\)]', '', phone)
    
    # Must start with + and have 10-15 digits
    pattern = r'^\+\d{10,15}$'
    
    return bool(re.match(pattern, cleaned))


def validate_username(username: str) -> tuple[bool, Optional[str]]:
    """
    Validate username format.
    
    Requirements:
    - 3-64 characters
    - Alphanumeric, underscore, hyphen only
    - Must start with a letter or number
    - Cannot start/end with underscore or hyphen
    
    Args:
        username: Username to validate
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not username or not isinstance(username, str):
        return False, 'Username is required'
    
    if len(username) < 3:
        return False, 'Username must be at least 3 characters long'
    
    if len(username) > 64:
        return False, 'Username must not exceed 64 characters'
    
    # Must be alphanumeric with optional underscores/hyphens
    if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9_-]*[a-zA-Z0-9]$', username):
        return False, 'Username can only contain letters, numbers, underscores, and hyphens'
    
    # Reserved usernames
    reserved = ['admin', 'root', 'system', 'support', 'help', 'api', 'test']
    if username.lower() in reserved:
        return False, 'This username is reserved'
    
    return True, None


def sanitize_string(text: str, max_length: Optional[int] = None) -> str:
    """
    Sanitize user input string to prevent XSS attacks.
    
    Args:
        text: String to sanitize
        max_length: Optional maximum length
        
    Returns:
        str: Sanitized string
        
    Example:
        safe_name = sanitize_string(user_input, max_length=100)
    """
    if not text:
        return ''
    
    # HTML escape
    sanitized = html.escape(text.strip())
    
    # Truncate if needed
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized


def validate_url(url: str) -> bool:
    """
    Validate URL format.
    
    Args:
        url: URL to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not url or not isinstance(url, str):
        return False
    
    # Basic URL pattern
    pattern = r'^https?://(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$'
    
    return bool(re.match(pattern, url))


def validate_integer(value: any, min_value: Optional[int] = None, max_value: Optional[int] = None) -> tuple[bool, Optional[str]]:
    """
    Validate integer value with optional range.
    
    Args:
        value: Value to validate
        min_value: Optional minimum value
        max_value: Optional maximum value
        
    Returns:
        tuple: (is_valid, error_message)
    """
    try:
        int_value = int(value)
    except (ValueError, TypeError):
        return False, 'Must be a valid integer'
    
    if min_value is not None and int_value < min_value:
        return False, f'Must be at least {min_value}'
    
    if max_value is not None and int_value > max_value:
        return False, f'must not exceed {max_value}'
    
    return True, None
