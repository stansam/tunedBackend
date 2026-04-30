from flask import Blueprint

main_bp = Blueprint('main', __name__)

from tuned.apis.main.routes import ROUTES

for route in ROUTES:
    main_bp.add_url_rule(route['url_rule'], view_func=route['view_func'], methods=route['methods'])

__all__ = [
    'main_bp',
]
