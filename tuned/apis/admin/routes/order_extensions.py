from flask import request
from flask.views import MethodView
from flask_login import login_required, current_user
from dataclasses import asdict
from marshmallow import ValidationError
from tuned.utils.decorators import admin_required
from tuned.utils.responses import success_response, error_response
from tuned.apis.admin.schemas.orders import AdminRequestDeadlineExtensionSchema
from tuned.interface.admin.orders import AdminOrderService
from tuned.repository import Repository
from tuned.extensions import db
from tuned.core.logging import get_logger
from tuned.core.exceptions import NotFound
from tuned.models.enums import Priority

logger = get_logger(__name__)


def _make_service() -> AdminOrderService:
    return AdminOrderService(repos=Repository(db.session))


class AdminDeadlineExtensionsView(MethodView):
    decorators = [login_required, admin_required]

    def get(self, order_id: str):
        try:
            results = _make_service().get_deadline_extensions(order_id)
            return success_response(data=[asdict(r) for r in results], status=200)
        except Exception as exc:
            logger.error("[AdminDeadlineExtensionsView.get] %r", exc)
            return error_response("Failed to fetch extensions", status=500)

    def post(self, order_id: str):
        try:
            data = request.get_json() or {}
            try:
                validated = AdminRequestDeadlineExtensionSchema().load(data)
            except ValidationError:
                return error_response("Validation failed", status=400)
            result = _make_service().create_deadline_extension(
                order_id=order_id,
                requested_by=str(current_user.id),
                requested_hours=validated["requested_hours"],
                reason=validated["reason"],
                priority=Priority(validated.get("priority", Priority.NORMAL.value)),
            )
            return success_response(data=asdict(result), status=201)
        except NotFound as exc:
            return error_response(str(exc), status=404)
        except Exception as exc:
            logger.error("[AdminDeadlineExtensionsView.post] %r", exc)
            return error_response("Failed to create extension request", status=500)
