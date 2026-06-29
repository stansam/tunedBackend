from flask import Blueprint
from typing import cast, Callable, Any
from tuned.apis.legal.routes import PoliciesAPI, StatusAPI, AcceptAPI

legal_bp = Blueprint('legal', __name__)

ROUTES = [
    {"url_rule": "/policies", "view_func": PoliciesAPI.as_view("policies"), "methods": ["GET"]},
    {"url_rule": "/status", "view_func": StatusAPI.as_view("status"), "methods": ["GET"]},
    {"url_rule": "/accept", "view_func": AcceptAPI.as_view("accept"), "methods": ["POST"]},
]

for route in ROUTES:
    legal_bp.add_url_rule(
        rule=cast(str, route["url_rule"]),
        view_func=cast(Callable[..., Any], route["view_func"]),
        methods=cast(list[str], route["methods"])
    )
