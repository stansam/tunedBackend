import bcrypt
import secrets
import string
from typing import Tuple, Optional


def hash_password(password: str) -> str:
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt)
    
    return hashed.decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    try:
        password_bytes = password.encode('utf-8')
        hash_bytes = password_hash.encode('utf-8')
        
        return bcrypt.checkpw(password_bytes, hash_bytes)
    except Exception:
        return False


def check_password_strength(password: str) -> Tuple[bool, Optional[str]]:
    from tuned.utils.validators import validate_password_strength
    return validate_password_strength(password)


def generate_temporary_password(length: int = 16) -> str:
    uppercase = string.ascii_uppercase
    lowercase = string.ascii_lowercase
    digits = string.digits
    special = '!@#$%^&*()_+-='
    
    password = [
        secrets.choice(uppercase),
        secrets.choice(lowercase),
        secrets.choice(digits),
        secrets.choice(special)
    ]
    
    all_chars = uppercase + lowercase + digits + special
    password += [secrets.choice(all_chars) for _ in range(length - 4)]
    
    secrets.SystemRandom().shuffle(password)
    
    return ''.join(password)


def rehash_password_if_needed(password: str, current_hash: str, user) -> None:
    if not current_hash.startswith('$2b$'):
        user.set_password(password)
        from tuned.extensions import db
        db.session.commit()
