from flask import request
from flask.views import MethodView
from flask_login import login_required
from dataclasses import asdict
from marshmallow import ValidationError
from tuned.utils.decorators import admin_required
from tuned.utils.responses import (
    success_response, error_response, validation_error_response, created_response
)
from tuned.utils.dependencies import get_services
from tuned.extensions import db, socketio
from tuned.dtos import ServiceCategoryDTO
from tuned.core.logging import get_logger
from tuned.apis.admin.schemas import AdminServiceCategorySchema

logger = get_logger(__name__)


class AdminServiceCategoriesListView(MethodView):
    decorators = [login_required, admin_required]

    def get(self):
        try:
            cats = get_services().service_category.list_categories()
            return success_response(data=[asdict(c) for c in cats])
        except Exception as exc:
            logger.error("[AdminServiceCategoriesList.get] %r", exc)
            return error_response("Failed to fetch categories", status=500)

    def post(self):
        try:
            validated = AdminServiceCategorySchema().load(request.get_json() or {})
            dto = ServiceCategoryDTO(
                name=validated["name"],
                description=validated["description"],
                order=validated["order"]
            )
            res = get_services().service_category.create_category(dto)
            db.session.commit()
            socketio.emit("admin:category:created", asdict(res), to="admin_room")
            return created_response(data=asdict(res))
        except ValidationError as err:
            return validation_error_response(err.messages)
        except Exception as exc:
            db.session.rollback()
            logger.error("[AdminServiceCategoriesList.post] %r", exc)
            return error_response("Failed to create category", status=500)


class AdminPricingCategoriesListView(MethodView):
    decorators = [login_required, admin_required]

    def get(self):
        try:
            tiers = get_services().pricing_category.list_categories()
            return success_response(data=[asdict(t) for t in tiers])
        except Exception as exc:
            logger.error("[AdminPricingCategoriesList.get] %r", exc)
            return error_response("Failed to fetch pricing categories", status=500)
