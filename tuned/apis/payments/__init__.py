from flask import Blueprint
from typing import Callable, Any, cast

payments_bp = Blueprint("payments", __name__)

from tuned.apis.payments.routes import PAYMENT_ROUTES


for route in PAYMENT_ROUTES:
    payments_bp.add_url_rule(
        rule=cast(str, route["url_rule"]), 
        view_func=cast(Callable[..., Any], route["view_func"]), 
        methods=cast(list[str], route["methods"])
    )