from flask import request, make_response
from flask.views import MethodView
from flask_login import login_required
from dataclasses import asdict
from marshmallow import ValidationError
from tuned.utils.decorators import admin_required
from tuned.utils.responses import success_response, error_response
from tuned.interface.admin.users import AdminUserService
from tuned.apis.admin.schemas.users import (
    AdminUserListRequestSchema, BroadcastMessageSchema, DirectMessageSchema
)
from tuned.repository import Repository
from tuned.extensions import db
from tuned.core.logging import get_logger

logger = get_logger(__name__)


def _svc() -> AdminUserService:
    return AdminUserService(repos=Repository(db.session))


class AdminUsersListView(MethodView):
    decorators = [login_required, admin_required]
    def post(self):
        try:
            data = request.get_json() or {}
            try:
                dto = AdminUserListRequestSchema().load(data)
            except ValidationError as err:
                logger.warning("[AdminUsersListView] Validation failed: %r", err.messages)
                return error_response("Validation failed", status=400)
            result = _svc().list_users(dto)
            return success_response(data=asdict(result), status=200)
        except Exception as exc:
            logger.error("[AdminUsersListView] %r", exc)
            return error_response("Failed to fetch users", status=500)


class AdminUsersStatsView(MethodView):
    decorators = [login_required, admin_required]
    def get(self):
        try:
            result = _svc().get_stats()
            return success_response(data=asdict(result), status=200)
        except Exception as exc:
            logger.error("[AdminUsersStatsView] %r", exc)
            return error_response("Failed to fetch user stats", status=500)


class AdminUsersGeographyView(MethodView):
    decorators = [login_required, admin_required]
    def get(self):
        try:
            result = _svc().get_geography()
            return success_response(data=[asdict(d) for d in result], status=200)
        except Exception as exc:
            logger.error("[AdminUsersGeographyView] %r", exc)
            return error_response("Failed to fetch geography", status=500)


class AdminBroadcastView(MethodView):
    decorators = [login_required, admin_required]
    def post(self):
        try:
            data = request.get_json() or {}
            try:
                validated = BroadcastMessageSchema().load(data)
            except ValidationError as err:
                logger.warning("[AdminBroadcastView] Validation failed: %r", err.messages)
                return error_response("Validation failed", status=400)
            result = _svc().broadcast(validated["message"])
            return success_response(data=result, status=200)
        except Exception as exc:
            logger.error("[AdminBroadcastView] %r", exc)
            return error_response("Failed to broadcast", status=500)


class AdminMessageUserView(MethodView):
    decorators = [login_required, admin_required]
    def post(self, user_id: str):
        try:
            data = request.get_json() or {}
            try:
                validated = DirectMessageSchema().load(data)
            except ValidationError as err:
                logger.warning("[AdminMessageUserView] Validation failed: %r", err.messages)
                return error_response("Validation failed", status=400)
            result = _svc().message_user(user_id, validated["message"])
            return success_response(data=result, status=200)
        except Exception as exc:
            logger.error("[AdminMessageUserView] %r", exc)
            return error_response("Failed to send message", status=500)


class AdminUsersExportView(MethodView):
    decorators = [login_required, admin_required]
    def get(self):
        try:
            import csv, io
            from tuned.dtos.admin.users import AdminUserListRequestDTO
            dto = AdminUserListRequestDTO(per_page=1000, page=1)
            result = _svc().list_users(dto)
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=[
                "id", "name", "email", "orders_count",
                "total_spent", "clv_status", "status", "last_order_at"
            ])
            writer.writeheader()
            for user in result.users:
                # DTO contains avatar_url which we skip in CSV
                user_dict = asdict(user)
                if "avatar_url" in user_dict:
                    del user_dict["avatar_url"]
                writer.writerow(user_dict)
            response = make_response(output.getvalue())
            response.headers["Content-Type"] = "text/csv"
            response.headers["Content-Disposition"] = "attachment; filename=users.csv"
            return response
        except Exception as exc:
            logger.error("[AdminUsersExportView] %r", exc)
            return error_response("Failed to export users", status=500)
