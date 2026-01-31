"""
Main blueprint.

Routes for public-facing functionality:
- Landing page
- Public API endpoints
- Health checks
"""
from flask import Blueprint

main_bp = Blueprint('main', __name__)

# Import routes at the end to avoid circular imports
from tuned.main import routes
