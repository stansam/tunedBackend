"""
Password hashing and validation utilities using bcrypt.

Provides secure password management with:
- Bcrypt hashing with salt
- Password verification
- Strength validation
- Temporary password generation
"""
import bcrypt
import secrets
import string
from typing import Tuple, Optional


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt with automatic salt generation.
    
    Args:
        password: Plain text password
        
    Returns:
        str: Hashed password
        
    Example:
        hashed = hash_password('MySecurePassword123!')
    """
    # Encode password to bytes
    password_bytes = password.encode('utf-8')
    
    # Generate salt and hash password
    # Default work factor of 12 (2^12 = 4096 rounds)
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt)
    
    # Return as string
    return hashed.decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        password: Plain text password to verify
        password_hash: Previously hashed password
        
    Returns:
        bool: True if password matches, False otherwise
        
    Example:
        if verify_password(input_password, user.password_hash):
            # Password is correct
            pass
    """
    try:
        password_bytes = password.encode('utf-8')
        hash_bytes = password_hash.encode('utf-8')
        
        return bcrypt.checkpw(password_bytes, hash_bytes)
    except Exception:
        return False


def check_password_strength(password: str) -> Tuple[bool, Optional[str]]:
    """
    Check password strength against security policy.
    
    This is an alias to tuned.utils.validators.validate_password_strength
    for convenience in auth context.
    
    Args:
        password: Password to check
        
    Returns:
        tuple: (is_valid, error_message)
    """
    from tuned.utils.validators import validate_password_strength
    return validate_password_strength(password)


def generate_temporary_password(length: int = 16) -> str:
    """
    Generate a secure temporary password.
    
    Generated password includes:
    - Uppercase letters
    - Lowercase letters
    - Digits
    - Special characters
    
    Args:
        length: Password length (default: 16)
        
    Returns:
        str: Temporary password
        
    Example:
        temp_pass = generate_temporary_password()
        # Send to user via email for password reset
    """
    # Character sets
    uppercase = string.ascii_uppercase
    lowercase = string.ascii_lowercase
    digits = string.digits
    special = '!@#$%^&*()_+-='
    
    # Ensure at least one character from each set
    password = [
        secrets.choice(uppercase),
        secrets.choice(lowercase),
        secrets.choice(digits),
        secrets.choice(special)
    ]
    
    # Fill remaining length with random characters from all sets
    all_chars = uppercase + lowercase + digits + special
    password += [secrets.choice(all_chars) for _ in range(length - 4)]
    
    # Shuffle to avoid predictable pattern
    secrets.SystemRandom().shuffle(password)
    
    return ''.join(password)


def rehash_password_if_needed(password: str, current_hash: str, user) -> None:
    """
    Check if password needs rehashing (e.g., if work factor increased).
    If needed, rehash and update user model.
    
    This is a security best practice to ensure passwords use the latest
    hashing parameters.
    
    Args:
        password: Plain text password (during successful login)
        current_hash: Current password hash
        user: User model instance
        
    Example:
        if verify_password(password, user.password_hash):
            rehash_password_if_needed(password, user.password_hash, user)
    """
    # Check if hash needs updating (bcrypt version or work factor changed)
    # For now, we just ensure it's using bcrypt format
    # Future: check work factor and rehash if < 12
    
    if not current_hash.startswith('$2b$'):
        # Not bcrypt format, rehash
        user.set_password(password)
        from tuned.extensions import db
        db.session.commit()
