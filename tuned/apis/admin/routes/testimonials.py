from flask import request
from flask.views import MethodView
from flask_login import login_required, current_user
from dataclasses import asdict
from marshmallow import ValidationError

from tuned.utils.decorators import admin_required
from tuned.utils.responses import (
    success_response, error_response, validation_error_response, no_content_response
)
from tuned.utils.dependencies import get_services
from tuned.dtos import AdminTestimonialListRequestDTO, TestimonialUpdateDTO
from tuned.repository.exceptions import NotFound
from tuned.core.logging import get_logger
from tuned.apis.admin.schemas import AdminTestimonialFilterSchema, AdminTestimonialUpdateSchema

logger = get_logger(__name__)

class AdminTestimonialsListView(MethodView):
    decorators = [login_required, admin_required]

    def get(self):
        try:
            val = AdminTestimonialFilterSchema().load(request.args)
            req = AdminTestimonialListRequestDTO(
                page=val.get("page"), per_page=val.get("per_page"),
                status=val.get("status"), service_id=val.get("service_id"),
                rating=val.get("rating"), q=val.get("q"),
                sort=val.get("sort"), order=val.get("order")
            )
            res = get_services().testimonial.list_all_testimonials(req)
            return success_response(data=asdict(res))
        except ValidationError as err:
            logger.error("[AdminTestimonialsListView.get] ValidationError: %r", err)
            return validation_error_response(err.messages)
        except Exception as exc:
            logger.error("[AdminTestimonialsListView.get] %r", exc)
            return error_response("Failed to fetch testimonials", status=500)

class AdminTestimonialApproveView(MethodView):
    decorators = [login_required, admin_required]

    def patch(self, testimonial_id: str):
        try:
            res = get_services().testimonial.approve_testimonial(testimonial_id, actor_id=str(current_user.id))
            return success_response(data=asdict(res))
        except NotFound as exc:
            logger.error("[AdminTestimonialApproveView.patch] NotFound: %r", exc)
            return error_response(str(exc), status=404)
        except Exception as exc:
            logger.error("[AdminTestimonialApproveView.patch] %r", exc)
            return error_response("Failed to approve testimonial", status=500)

class AdminTestimonialDetailView(MethodView):
    decorators = [login_required, admin_required]

    def put(self, testimonial_id: str):
        try:
            val = AdminTestimonialUpdateSchema().load(request.get_json() or {})
            dto = TestimonialUpdateDTO(
                content=val.get("content"), rating=val.get("rating"), is_approved=val.get("is_approved")
            )
            res = get_services().testimonial.update_testimonial(testimonial_id, dto, actor_id=str(current_user.id))
            return success_response(data=asdict(res))
        except ValidationError as err:
            logger.error("[AdminTestimonialDetailView.put] ValidationError: %r", err)
            return validation_error_response(err.messages)
        except NotFound as exc:
            logger.error("[AdminTestimonialDetailView.put] NotFound: %r", exc)
            return error_response(str(exc), status=404)
        except Exception as exc:
            logger.error("[AdminTestimonialDetailView.put] %r", exc)
            return error_response("Failed to update testimonial", status=500)

    def delete(self, testimonial_id: str):
        try:
            get_services().testimonial.delete_testimonial(testimonial_id, actor_id=str(current_user.id))
            return no_content_response()
        except NotFound as exc:
            logger.error("[AdminTestimonialDetailView.delete] NotFound: %r", exc)
            return error_response(str(exc), status=404)
        except Exception as exc:
            logger.error("[AdminTestimonialDetailView.delete] %r", exc)
            return error_response("Failed to delete testimonial", status=500)
