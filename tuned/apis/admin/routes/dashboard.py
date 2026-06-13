from flask.views import MethodView
from flask_login import login_required
from tuned.utils.decorators import admin_required
from tuned.utils.responses import success_response, error_response
from tuned.utils.dependencies import get_services
from tuned.core.logging import get_logger
from tuned.apis.admin.schemas.dashboard import (
    AdminKPIResponseSchema, AdminAnalyticsResponseSchema,
    AdminTrackingResponseSchema, AdminAlertsResponseSchema
)

logger = get_logger(__name__)


class AdminKPIView(MethodView):
    decorators = [login_required, admin_required]
    
    def get(self):
        try:
            dto = get_services().analytics.admin.get_kpis()
            data = AdminKPIResponseSchema().dump(dto)
            return success_response(data=data, status=200)
        except Exception as exc:
            logger.error("[AdminKPIView] %r", exc)
            return error_response(message="Failed to fetch KPIs", status=500)


class AdminAnalyticsView(MethodView):
    decorators = [login_required, admin_required]
    
    def get(self):
        try:
            dto = get_services().analytics.admin.get_analytics()
            data = AdminAnalyticsResponseSchema().dump(dto)
            return success_response(data=data, status=200)
        except Exception as exc:
            logger.error("[AdminAnalyticsView] %r", exc)
            return error_response(message="Failed to fetch analytics", status=500)


class AdminTrackingView(MethodView):
    decorators = [login_required, admin_required]
    
    def get(self):
        try:
            dto = get_services().analytics.admin.get_tracking()
            data = AdminTrackingResponseSchema().dump(dto)
            return success_response(data=data, status=200)
        except Exception as exc:
            logger.error("[AdminTrackingView] %r", exc)
            return error_response(message="Failed to fetch tracking", status=500)


class AdminAlertsView(MethodView):
    decorators = [login_required, admin_required]
    
    def get(self):
        try:
            dto = get_services().analytics.admin.get_alerts()
            data = AdminAlertsResponseSchema().dump(dto)
            return success_response(data=data, status=200)
        except Exception as exc:
            logger.error("[AdminAlertsView] %r", exc)
            return error_response(message="Failed to fetch alerts", status=500)
