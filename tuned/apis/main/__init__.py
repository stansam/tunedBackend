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
from tuned.apis.main.routes import ROUTES

for route in ROUTES:
    main_bp.add_url_rule(route['url_rule'], view_func=route['view_func'], methods=route['methods'])

__all__ = [
    'main_bp',
]
