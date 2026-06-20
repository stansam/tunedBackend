from flask import request
from flask.views import MethodView
from flask_login import login_required, current_user
from dataclasses import asdict
from marshmallow import ValidationError
from tuned.utils.decorators import admin_required
from tuned.utils.responses import success_response, error_response
from tuned.apis.admin.schemas.orders import AdminUpdateRevisionStatusSchema
from tuned.interface.admin.orders import AdminOrderService
from tuned.repository import Repository
from tuned.extensions import db
from tuned.core.logging import get_logger
from tuned.core.exceptions import NotFound
from tuned.models.enums import RevisionRequestStatus

logger = get_logger(__name__)


def _make_service() -> AdminOrderService:
    return AdminOrderService(repos=Repository(db.session))


class AdminOrderDetailView(MethodView):
    decorators = [login_required, admin_required]

    def get(self, order_number: str):
        try:
            result = _make_service().get_order_detail(order_number)
            return success_response(data=asdict(result), status=200)
        except NotFound as exc:
            return error_response(str(exc), status=404)
        except Exception as exc:
            logger.error("[AdminOrderDetailView] %r", exc)
            return error_response("Failed to fetch order", status=500)


class AdminOrderRevisionRequestsView(MethodView):
    decorators = [login_required, admin_required]

    def get(self, order_id: str):
        try:
            results = _make_service().get_revision_requests(order_id)
            return success_response(data=[asdict(r) for r in results], status=200)
        except Exception as exc:
            logger.error("[AdminOrderRevisionRequestsView] %r", exc)
            return error_response("Failed to fetch revision requests", status=500)


class AdminUpdateRevisionStatusView(MethodView):
    decorators = [login_required, admin_required]

    def patch(self, order_id: str, request_id: str):
        try:
            data = request.get_json() or {}
            try:
                validated = AdminUpdateRevisionStatusSchema().load(data)
            except ValidationError:
                return error_response("Validation failed", status=400)
            result = _make_service().update_revision_request_status(
                order_id=order_id,
                request_id=request_id,
                reviewed_by=str(current_user.id),
                new_status=RevisionRequestStatus(validated["status"]),
                internal_notes=validated.get("internal_notes"),
            )
            return success_response(data=asdict(result), status=200)
        except NotFound as exc:
            return error_response(str(exc), status=404)
        except ValueError as exc:
            return error_response(str(exc), status=400)
        except Exception as exc:
            logger.error("[AdminUpdateRevisionStatusView] %r", exc)
            return error_response("Failed to update revision status", status=500)
