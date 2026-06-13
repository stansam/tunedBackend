from flask.views import MethodView
from flask_login import login_required
from dataclasses import asdict
from tuned.utils.decorators import admin_required
from tuned.utils.responses import success_response, error_response
from tuned.utils.dependencies import get_services
from tuned.core.logging import get_logger

logger = get_logger(__name__)


class AdminNavStatsView(MethodView): # TODO: Check on payments count and chat count correctness.
    decorators = [login_required, admin_required]

    def get(self):
        try:
            services = get_services()
            service = services.analytics.admin
            dto = service.get_nav_stats()
            return success_response(data=asdict(dto), status=200)
        except Exception as exc:
            logger.error("[AdminNavStatsView] Failed: %r", exc)
            return error_response(message="Failed to fetch nav stats", status=500)
