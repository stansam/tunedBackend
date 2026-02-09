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

from tuned.auth import routes
