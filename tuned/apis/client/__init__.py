from flask import Blueprint

client_bp = Blueprint("client", __name__)

from tuned.apis.client.routes import CLIENT_ROUTES  # noqa: E402

for route in CLIENT_ROUTES:
    client_bp.add_url_rule(**route)

