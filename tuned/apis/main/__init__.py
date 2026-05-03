from flask import Blueprint
from typing import Any, Callable, cast

main_bp = Blueprint('main', __name__)

from tuned.apis.main.routes import ROUTES

for route in ROUTES:
    main_bp.add_url_rule(
        rule=cast(str, route['url_rule']), 
        view_func=cast(Callable[..., Any], route['view_func']), 
        methods=cast(list[str], route['methods'])
    )

__all__ = [
    'main_bp',
]
