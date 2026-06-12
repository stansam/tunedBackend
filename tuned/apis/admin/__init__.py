from flask import Blueprint

admin_bp = Blueprint("admin", __name__)

from tuned.apis.admin.routes import ADMIN_ROUTES

for route in ADMIN_ROUTES:
    admin_bp.add_url_rule(
        route["url_rule"],
        view_func=route["view_func"],
        methods=route["methods"],
    )
