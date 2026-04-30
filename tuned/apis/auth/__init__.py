from flask import Blueprint

auth_bp = Blueprint('auth', __name__)

from tuned.apis.auth.routes import ROUTES

for route in ROUTES:
    auth_bp.add_url_rule(
        rule=route['url_rule'], 
        view_func=route['view_func'], 
        methods=route['methods']
    )

__all__ = [
    'auth_bp',
]