from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from flask import current_app
from typing import Optional, Dict, Any
import secrets
import string


def get_serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'])


def generate_token(data: Dict[str, Any], salt: str) -> str:
    serializer = get_serializer()
    return serializer.dumps(data, salt=salt)


def verify_token(token: str, salt: str, max_age: int = 3600) -> Optional[Dict[str, Any]]:
    serializer = get_serializer()
    
    try:
        data: Dict[str, Any] = serializer.loads(token, salt=salt, max_age=max_age)
        return data
    except (SignatureExpired, BadSignature):
        return None


def generate_verification_token(user_id: int, email: str) -> str:
    return generate_token(
        {'user_id': user_id, 'email': email},
        salt='email-verification'
    )


def verify_verification_token(token: str) -> Optional[Dict[str, Any]]:
    # 24 hours = 86400 seconds
    return verify_token(token, salt='email-verification', max_age=86400)


def generate_password_reset_token(user_id: int, email: str) -> str:
    return generate_token(
        {'user_id': user_id, 'email': email},
        salt='password-reset'
    )


def verify_password_reset_token(token: str) -> Optional[Dict[str, Any]]:
    # 1 hour = 3600 seconds
    return verify_token(token, salt='password-reset', max_age=3600)


def generate_referral_code(length: int = 8) -> str:
    chars = string.ascii_uppercase + string.digits
    chars = chars.replace('0', '').replace('O', '').replace('I', '').replace('1', '')
    
    return ''.join(secrets.choice(chars) for _ in range(length))


def generate_secure_random_string(length: int = 32) -> str:
    return secrets.token_hex(length // 2)
