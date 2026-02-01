"""
Admin blueprint.

Routes for admin functionality:
- Dashboard
- Order management
- User management
- Revenue & analytics
- Revision request management
- Deadline extension management
"""
from flask import Blueprint

admin_bp = Blueprint('admin', __name__)

# Import routes to register them
from tuned.admin.routes import revision_requests, deadline_extensions