from flask import request
from flask.views import MethodView
from flask_login import login_required
from dataclasses import asdict
from marshmallow import ValidationError
from tuned.utils.decorators import admin_required
from tuned.utils.responses import success_response, error_response, validation_error_response, no_content_response
from tuned.utils.dependencies import get_services
from tuned.extensions import db, socketio
from tuned.dtos import ServiceUpdateDTO, ServiceCategoryUpdateDTO
from tuned.core.logging import get_logger
from tuned.apis.admin.schemas import AdminServiceCategoryUpdateSchema, AdminServiceUpdateSchema

logger = get_logger(__name__)

class AdminServiceCategoryDetailView(MethodView):
    decorators = [login_required, admin_required]

    def put(self, category_id: str):
        try:
            validated = AdminServiceCategoryUpdateSchema().load(request.get_json() or {})
            dto = ServiceCategoryUpdateDTO(name=validated.get("name"), description=validated.get("description"), order=validated.get("order"))
            res = get_services().service_category.update_category(category_id, dto)
            db.session.commit()
            socketio.emit("admin:category:updated", asdict(res), to="admin_room")
            return success_response(data=asdict(res))
        except ValidationError as err:
            return validation_error_response(err.messages)
        except Exception as exc:
            db.session.rollback()
            logger.error("[AdminServiceCategoryDetail.put] %r", exc)
            return error_response("Failed to update category", status=500)

    def delete(self, category_id: str):
        try:
            get_services().service_category.delete_category(category_id)
            db.session.commit()
            socketio.emit("admin:category:deleted", {"id": category_id}, to="admin_room")
            return no_content_response()
        except Exception as exc:
            db.session.rollback()
            logger.error("[AdminServiceCategoryDetail.delete] %r", exc)
            return error_response("Failed to delete category", status=500)

class AdminServiceDetailView(MethodView):
    decorators = [login_required, admin_required]

    def put(self, service_id: str):
        try:
            validated = AdminServiceUpdateSchema().load(request.get_json() or {})
            dto = ServiceUpdateDTO(
                name=validated.get("name"), description=validated.get("description"), category_id=validated.get("category_id"),
                featured=validated.get("featured"), pricing_category_id=validated.get("pricing_category_id"),
                slug=validated.get("slug"), is_active=validated.get("is_active"), tags=validated.get("tags")
            )
            res = get_services().service.update_service(service_id, dto)
            db.session.commit()
            socketio.emit("admin:service:updated", asdict(res), to="admin_room")
            return success_response(data=asdict(res))
        except ValidationError as err:
            return validation_error_response(err.messages)
        except Exception as exc:
            db.session.rollback()
            logger.error("[AdminServiceDetail.put] %r", exc)
            return error_response("Failed to update service", status=500)

    def delete(self, service_id: str):
        try:
            get_services().service.delete_service(service_id)
            db.session.commit()
            socketio.emit("admin:service:deleted", {"id": service_id}, to="admin_room")
            return no_content_response()
        except Exception as exc:
            db.session.rollback()
            logger.error("[AdminServiceDetail.delete] %r", exc)
            return error_response("Failed to delete service", status=500)
