"""
Authentication blueprint.

Routes for user authentication:
- Login/Logout
- Registration
- Password reset
- Email verification
"""
from flask import Blueprint

auth_bp = Blueprint('auth', __name__)

from tuned.apis.auth.routes import ROUTES

for route in ROUTES:
    auth_bp.add_url_rule(route['url_rule'], view_func=route['view_func'], methods=route['methods'])

__all__ = [
    'auth_bp',
]