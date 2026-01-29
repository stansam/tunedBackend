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

# Import routes to register them with the blueprint
from tuned.auth import routes
