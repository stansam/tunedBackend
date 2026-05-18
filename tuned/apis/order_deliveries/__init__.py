from flask import Blueprint
from typing import cast, Callable, Any

order_deliveries_bp = Blueprint("order_deliveries", __name__)

from tuned.apis.order_deliveries.routes import DELIVERY_ROUTES

for route in DELIVERY_ROUTES:
    order_deliveries_bp.add_url_rule(
        rule=cast(str, route["url_rule"]), 
        view_func=cast(Callable[..., Any], route["view_func"]), 
        methods=cast(list[str], route["methods"])
    )