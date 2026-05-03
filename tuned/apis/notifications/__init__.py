from flask import Blueprint
from typing import cast, Callable, Any

notification_bp = Blueprint('notifications', __name__, url_prefix='/notifications')

from tuned.apis.notifications.routes import ROUTES

for route in ROUTES:
    notification_bp.add_url_rule(
        rule=cast(str, route["url_rule"]), 
        view_func=cast(Callable[..., Any], route["view_func"]), 
        methods=cast(list[str], route["methods"])
    )
