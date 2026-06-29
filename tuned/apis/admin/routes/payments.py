from flask import request
from flask.views import MethodView
from flask_login import login_required
from marshmallow import ValidationError
from tuned.utils.decorators import admin_required
from tuned.utils.responses import success_response, error_response
from tuned.apis.admin.schemas.payments import (
    AdminPaymentListRequestSchema, AdminPaymentListResponseSchema
)
from tuned.interface.admin.payments import AdminPaymentService
from tuned.repository import Repository
from tuned.extensions import db
from tuned.core.logging import get_logger

logger = get_logger(__name__)

def _make_service() -> AdminPaymentService:
    return AdminPaymentService(repos=Repository(db.session))

class AdminPaymentsListView(MethodView):
    decorators = [login_required, admin_required]

    def post(self):
        try:
            data = request.get_json() or {}
            try:
                req_dto = AdminPaymentListRequestSchema().load(data)
            except ValidationError as err:
                logger.warning("[AdminPaymentsListView] Validation failed: %r", err.messages)
                return error_response(message="Validation failed", status=400)

            result = _make_service().list_payments(req_dto)
            response_data = AdminPaymentListResponseSchema().dump(result)
            return success_response(data=response_data, status=200)
        except Exception as exc:
            logger.error("[AdminPaymentsListView] %r", exc)
            return error_response("Failed to fetch payments", status=500)
