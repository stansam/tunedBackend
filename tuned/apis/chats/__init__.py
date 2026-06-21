from flask import Blueprint
from typing import cast, Callable, Any

chats_bp = Blueprint("chats", __name__)

from tuned.apis.chats.routes import CHAT_ROUTES

for route in CHAT_ROUTES:
    chats_bp.add_url_rule(
        rule=cast(str, route["url_rule"]), 
        view_func=cast(Callable[..., Any], route["view_func"]), 
        methods=cast(list[str], route["methods"])
    )
