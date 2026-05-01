
from flask import request

def get_user_ip() -> str:
    forwarded = request.headers.get('X-Forwarded-For')
    if forwarded:
        return forwarded.split(',')[0].strip()
    
    real_ip = request.headers.get('X-Real-IP')
    if real_ip:
        return real_ip
    
    return request.remote_addr or 'unknown'

def get_user_agent() -> str:
    return request.headers.get('User-Agent', 'unknown')


def is_email_verified_required() -> bool:
    from flask import current_app
    return bool(current_app.config.get('REQUIRE_EMAIL_VERIFICATION', True))
