"""
Client blueprint.

Routes for client-facing functionality:
- Dashboard
- Orders
- Payments
- Profile management
"""
from flask import Blueprint

client_bp = Blueprint('client', __name__)

# Import routes at the end to avoid circular imports
# from . import routes
