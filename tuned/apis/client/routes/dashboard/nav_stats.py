from tuned.interface import analytics as _analytics_service
import logging
from tuned.core.logging import get_logger
from tuned.utils.responses import success_response, error_response
from flask_login import login_required, current_user
from flask.views import MethodView
from dataclasses import asdict

logger: logging.Logger = get_logger(__name__)

class NavStats(MethodView):
    decorators = [login_required]

    def get(self):
        try:
            dto = _analytics_service.get_nav_stats(str(current_user.id))
            return success_response(data=asdict(dto), message="Successfully loaded", status=200)
        except Exception as e:
            logger.error("Failed to load nav stats: %s", e)
            return error_response(message="Failed to load nav stats", status=500)
