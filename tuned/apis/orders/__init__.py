from flask import Blueprint
from typing import cast, Callable, Any

orders_bp = Blueprint("orders", __name__)

from tuned.apis.orders.routes import ORDER_ROUTES

for route in ORDER_ROUTES:
    orders_bp.add_url_rule(
        rule=cast(str, route["url_rule"]), 
        view_func=cast(Callable[..., Any], route["view_func"]), 
        methods=cast(list[str], route["methods"])
    )
