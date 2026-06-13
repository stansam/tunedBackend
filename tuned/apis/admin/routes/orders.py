from flask import request
from flask.views import MethodView
from flask_login import login_required
from dataclasses import asdict
from marshmallow import ValidationError
from tuned.utils.decorators import admin_required
from tuned.utils.responses import success_response, error_response
from tuned.apis.admin.schemas.orders import AdminOrderListRequestSchema
from tuned.interface.admin.orders import AdminOrderService
from tuned.repository import Repository
from tuned.extensions import db
from tuned.core.logging import get_logger
from tuned.core.exceptions import NotFound

logger = get_logger(__name__)


def _make_service() -> AdminOrderService:
    return AdminOrderService(repos=Repository(db.session))


class AdminOrdersListView(MethodView):
    decorators = [login_required, admin_required]

    def post(self):
        try:
            data = request.get_json() or {}
            try:
                req_dto = AdminOrderListRequestSchema().load(data)
            except ValidationError as err:
                logger.warning("[AdminOrdersListView] Validation failed: %r", err.messages)
                return error_response(message="Validation failed", status=400)
            
            result = _make_service().list_all_orders(req_dto)
            return success_response(data=asdict(result), status=200)
        except Exception as exc:
            logger.error("[AdminOrdersListView] %r", exc)
            return error_response("Failed to fetch orders", status=500)


class AdminOrdersStatsView(MethodView):
    decorators = [login_required, admin_required]

    def get(self):
        try:
            result = _make_service().get_orders_stats()
            return success_response(data=asdict(result), status=200)
        except Exception as exc:
            logger.error("[AdminOrdersStatsView] %r", exc)
            return error_response("Failed to fetch order stats", status=500)


class AdminActivateOrderView(MethodView):
    decorators = [login_required, admin_required]

    def post(self, order_id: str):
        try:
            result = _make_service().activate_order(order_id)
            return success_response(data=result, status=200)
        except NotFound as exc:
            return error_response(str(exc), status=404)
        except ValueError as exc:
            return error_response(str(exc), status=400)
        except Exception as exc:
            logger.error("[AdminActivateOrderView] %r", exc)
            return error_response("Failed to activate order", status=500)


class AdminEscalateOrderView(MethodView):
    decorators = [login_required, admin_required]

    def post(self, order_id: str):
        try:
            result = _make_service().escalate_order(order_id)
            return success_response(data=result, status=200)
        except NotFound as exc:
            return error_response(str(exc), status=404)
        except Exception as exc:
            logger.error("[AdminEscalateOrderView] %r", exc)
            return error_response("Failed to escalate order", status=500)
