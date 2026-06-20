from flask import Blueprint

media_bp = Blueprint("media", __name__)

from tuned.apis.media.routes import MEDIA_ROUTES

for route in MEDIA_ROUTES:
    media_bp.add_url_rule(
        rule=route["rule"],
        view_func=route["view_func"],
        methods=route["methods"]
    )