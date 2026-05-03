import logging
from tuned.utils.dependencies import get_services
from tuned.core.logging import get_logger
from tuned.utils.responses import success_response, error_response
from flask_login import login_required, current_user
from flask.views import MethodView
from dataclasses import asdict
from typing import Any

logger: logging.Logger = get_logger(__name__)

class DashboardTracking(MethodView):
    decorators = [login_required]

    def get(self) -> tuple[Any, int]:
        try:
            dto = get_services().analytics.get_tracking(current_user.id)
            return success_response(data=asdict(dto), message="Successfully loaded", status=200)
        except Exception as e:
            logger.error("Failed to load tracking: %s", e)
            return error_response(message="Failed to load tracking", status=500)
