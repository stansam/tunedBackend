from flask import Blueprint

notification_bp = Blueprint('notifications', __name__, url_prefix='/notifications')

from tuned.apis.notifications.routes import ROUTES

for route in ROUTES:
    notification_bp.add_url_rule(route["url_rule"], view_func=route["view_func"], methods=route["methods"])
