"""
Admin blueprint.

Routes for admin functionality:
- User management
- Order management
- Content management
- System settings
"""
from flask import Blueprint

admin_bp = Blueprint('admin', __name__)

# Import routes at the end to avoid circular imports
# from . import routes