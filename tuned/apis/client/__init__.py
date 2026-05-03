from flask import Blueprint

client_bp = Blueprint("client", __name__)

from tuned.apis.client.routes import CLIENT_ROUTES

for route in CLIENT_ROUTES:
    client_bp.add_url_rule(
        rule=route["rule"],
        view_func=route["view_func"],
        methods=route["methods"]
    )

