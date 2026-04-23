import logging
from tuned.core.logging import get_logger
from tuned.utils.responses import success_response, error_response
from tuned.interface import order as _order_service
from flask_login import login_required, current_user
from flask.views import MethodView
from dataclasses import asdict

logger: logging.Logger = get_logger(__name__)

class DashboardAnalytics(MethodView):
    decorators = [login_required]

    def get(self):
        try:
            dto = _order_service.get_analytics(str(current_user.id))
            return success_response("Successfully loaded", status=200, data=asdict(dto))
        except Exception as e:
            logger.error("Failed to load analytics: %s", e)
            return error_response("Failed to load analytics", status=500)
