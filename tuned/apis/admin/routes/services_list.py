from flask import request
from flask.views import MethodView
from flask_login import login_required
from dataclasses import asdict
from marshmallow import ValidationError
from typing import Any

from tuned.utils.decorators import admin_required
from tuned.utils.responses import (
    success_response, error_response, validation_error_response, created_response
)
from tuned.utils.dependencies import get_services
from tuned.extensions import db, socketio
from tuned.dtos import ServiceDTO, ServiceResponseDTO
from tuned.core.logging import get_logger
from tuned.apis.admin.schemas.services import AdminServiceSchema

logger = get_logger(__name__)


def filter_services(
    services: list[ServiceResponseDTO], args: dict[str, Any]
) -> list[ServiceResponseDTO]:
    q = args.get("q", "").strip().lower()
    cat_id = args.get("category_id", "").strip()
    is_act = args.get("is_active", "").strip().lower()
    feat = args.get("featured", "").strip().lower()

    res = []
    for s in services:
        if q and (
            q not in s.name.lower()
            and q not in (s.description or "").lower()
            and q not in s.slug.lower()
        ):
            continue
        if cat_id and s.category_id != cat_id:
            continue
        if is_act == "true" and not s.is_active:
            continue
        if is_act == "false" and s.is_active:
            continue
        if feat == "true" and not s.featured:
            continue
        if feat == "false" and s.featured:
            continue
        res.append(s)
    return res


class AdminServicesListView(MethodView):
    decorators = [login_required, admin_required]

    def get(self):
        try:
            services = get_services().service.list_services(active_only=False)
            filtered = filter_services(services, request.args)
            return success_response(data=[asdict(s) for s in filtered])
        except Exception as exc:
            logger.error("[AdminServicesList.get] %r", exc)
            return error_response("Failed to fetch services", status=500)

    def post(self):
        try:
            validated = AdminServiceSchema().load(request.get_json() or {})
            dto = ServiceDTO(
                name=validated["name"],
                description=validated["description"],
                category_id=validated["category_id"],
                featured=validated["featured"],
                pricing_category_id=validated["pricing_category_id"],
                slug=validated.get("slug"),
                is_active=validated["is_active"],
                tags=validated["tags"],
            )
            res = get_services().service.create_service(dto)
            db.session.commit()
            socketio.emit("admin:service:created", asdict(res), to="admin_room")
            return created_response(data=asdict(res))
        except ValidationError as err:
            return validation_error_response(err.messages)
        except Exception as exc:
            db.session.rollback()
            logger.error("[AdminServicesList.post] %r", exc)
            return error_response("Failed to create service", status=500)
