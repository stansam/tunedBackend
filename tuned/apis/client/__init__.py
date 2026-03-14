"""
Client blueprint.

Routes for client-facing functionality:
- Dashboard
- Orders
- Payments
- Profile management
- Revision requests
- Deadline extensions
"""
from flask import Blueprint

client_bp = Blueprint('client', __name__)

# Import routes at the end to avoid circular imports
from tuned.client.routes import revision_requests, deadline_extensions


