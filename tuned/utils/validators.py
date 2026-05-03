import re
from typing import Optional, Any
import html


def validate_email(email: str) -> bool:
    if not email or not isinstance(email, str):
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if len(email) > 320:
        return False
    
    if '..' in email:
        return False
        
    return bool(re.match(pattern, email.strip()))


def validate_password_strength(password: str) -> tuple[bool, Optional[str]]:
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
    
    common_passwords = ['password', '12345678', 'password123', 'qwerty123']
    if password.lower() in common_passwords:
        return False, 'Password is too common, please choose a stronger password'
    
    return True, None


def validate_phone_number(phone: str) -> bool:
    if not phone or not isinstance(phone, str):
        return False
    
    cleaned = re.sub(r'[\s\-\(\)]', '', phone)
    
    pattern = r'^\+\d{10,15}$'
    
    return bool(re.match(pattern, cleaned))


def validate_username(username: str) -> tuple[bool, Optional[str]]:
    if not username or not isinstance(username, str):
        return False, 'Username is required'
    
    if len(username) < 3:
        return False, 'Username must be at least 3 characters long'
    
    if len(username) > 64:
        return False, 'Username must not exceed 64 characters'
    
    if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9_-]*[a-zA-Z0-9]$', username):
        return False, 'Username can only contain letters, numbers, underscores, and hyphens'
    
    reserved = ['admin', 'root', 'system', 'support', 'help', 'api', 'test']
    if username.lower() in reserved:
        return False, 'This username is reserved'
    
    return True, None


def sanitize_string(text: str, max_length: Optional[int] = None) -> str:
    if not text:
        return ''
    
    sanitized = html.escape(text.strip())
    
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized


def validate_url(url: str) -> bool:
    if not url or not isinstance(url, str):
        return False
    
    pattern = r'^https?://(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$'
    
    return bool(re.match(pattern, url))


def validate_integer(value: Any, min_value: Optional[int] = None, max_value: Optional[int] = None) -> tuple[bool, Optional[str]]:
    try:
        int_value = int(value)
    except (ValueError, TypeError):
        return False, 'Must be a valid integer'
    
    if min_value is not None and int_value < min_value:
        return False, f'Must be at least {min_value}'
    
    if max_value is not None and int_value > max_value:
        return False, f'must not exceed {max_value}'
    
    return True, None
