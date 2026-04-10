
from flask import request

def get_user_ip() -> str:
    if request.headers.get('X-Forwarded-For'):
        ip = request.headers.get('X-Forwarded-For').split(',')[0].strip()
    elif request.headers.get('X-Real-IP'):
        ip = request.headers.get('X-Real-IP')
    else:
        ip = request.remote_addr
    
    return ip or 'unknown'

def get_user_agent() -> str:
    return request.headers.get('User-Agent', 'unknown')


def is_email_verified_required() -> bool:
    from flask import current_app
    return current_app.config.get('REQUIRE_EMAIL_VERIFICATION', True)
