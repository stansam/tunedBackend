from flask import request
from flask.views import MethodView
from flask_login import login_required, current_user
from dataclasses import asdict
from marshmallow import ValidationError

from tuned.utils.decorators import admin_required
from tuned.utils.responses import (
    success_response, error_response, validation_error_response, created_response, no_content_response
)
from tuned.utils.dependencies import get_services
from tuned.dtos import SampleDTO, SampleUpdateDTO, SampleListRequestDTO
from tuned.repository.exceptions import NotFound, AlreadyExists
from tuned.core.logging import get_logger
from tuned.apis.admin.schemas.samples import AdminSampleSchema, AdminSampleUpdateSchema
from tuned.apis.main.schemas.samples import SampleFilterSchema

logger = get_logger(__name__)


class AdminSamplesListView(MethodView):
    decorators = [login_required, admin_required]

    def get(self):
        try:
            validated = SampleFilterSchema().load(request.args)
            req_dto = SampleListRequestDTO(
                q=validated.get("q"),
                service_id=validated.get("service_id"),
                featured=validated.get("featured"),
                sort=validated.get("sort"),
                order=validated.get("order"),
                page=validated.get("page"),
                per_page=validated.get("per_page")
            )
            res = get_services().sample.list_samples(req_dto)
            return success_response(data=asdict(res))
        except ValidationError as err:
            logger.error("[AdminSamplesListView.get] Validation Error: %r", err)
            return validation_error_response(err.messages)
        except Exception as exc:
            logger.error("[AdminSamplesListView.get] %r", exc)
            return error_response("Failed to fetch samples", status=500)

    def post(self):
        try:
            validated = AdminSampleSchema().load(request.get_json() or {})
            dto = SampleDTO(
                title=validated["title"],
                content=validated["content"],
                service_id=validated["service_id"],
                excerpt=validated["excerpt"],
                word_count=validated["word_count"],
                featured=validated["featured"],
                image=validated["image"],
                slug=validated.get("slug"),
                tags=validated["tags"]
            )
            res = get_services().sample.create_sample(dto, actor_id=str(current_user.id))
            return created_response(data=asdict(res))
        except ValidationError as err:
            return validation_error_response(err.messages)
        except AlreadyExists as exc:
            return error_response(str(exc), status=400)
        except Exception as exc:
            logger.error("[AdminSamplesListView.post] %r", exc)
            return error_response("Failed to create sample", status=500)


class AdminSampleDetailView(MethodView):
    decorators = [login_required, admin_required]

    def put(self, sample_id: str):
        try:
            validated = AdminSampleUpdateSchema().load(request.get_json() or {})
            dto = SampleUpdateDTO(
                title=validated.get("title"),
                content=validated.get("content"),
                service_id=validated.get("service_id"),
                excerpt=validated.get("excerpt"),
                word_count=validated.get("word_count"),
                featured=validated.get("featured"),
                image=validated.get("image"),
                slug=validated.get("slug"),
                tags=validated.get("tags")
            )
            res = get_services().sample.update_sample(sample_id, dto, actor_id=str(current_user.id))
            return success_response(data=asdict(res))
        except ValidationError as err:
            return validation_error_response(err.messages)
        except NotFound as exc:
            return error_response(str(exc), status=404)
        except AlreadyExists as exc:
            return error_response(str(exc), status=400)
        except Exception as exc:
            logger.error("[AdminSampleDetailView.put] %r", exc)
            return error_response("Failed to update sample", status=500)

    def delete(self, sample_id: str):
        try:
            get_services().sample.delete_sample(sample_id, actor_id=str(current_user.id))
            return no_content_response()
        except NotFound as exc:
            return error_response(str(exc), status=404)
        except Exception as exc:
            logger.error("[AdminSampleDetailView.delete] %r", exc)
            return error_response("Failed to delete sample", status=500)
