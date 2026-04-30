from tuned.dtos import SampleListRequestDTO
from tuned.core.logging import get_logger
from flask.views import MethodView
from flask import request
from tuned.utils.dependencies import get_services
from tuned.utils.responses import success_response, error_response, paginated_response, validation_error_response
from tuned.apis.main.schemas import SampleFilterSchema
from tuned.redis_client import redis_client
from marshmallow import ValidationError
from dataclasses import asdict
import json
import logging
from typing import Any

logger: logging.Logger = get_logger(__name__)

CACHE_TTL = 300
CACHE_KEY_SAMPLES = 'samples:list'


class SampleListView(MethodView):
    def __init__(self) -> None:
        self._schema = SampleFilterSchema()

    def get(self) -> tuple[Any, int]:
        try:
            params = {}
            if request.args:
                params = self._schema.load(request.args)
            
        except ValidationError as err:
            logger.error(f'Validation error: {str(err)}')
            return validation_error_response(err.messages)

        try:
            cache_key = f"{CACHE_KEY_SAMPLES}:{json.dumps(params)}"
            cached_data = redis_client.get(cache_key)
            if cached_data:
                data = json.loads(cached_data)
                logger.info(f'Samples fetched from cache: page {data.get("page")}, total {data.get("total")}')

                return paginated_response(
                    items=data.get("samples"),
                    page=data.get("page", 1),
                    per_page=data.get("per_page", 12),
                    total=data.get("total")
                )

            samples_dto = SampleListRequestDTO(**params)
            samples = get_services().sample.list_samples(samples_dto)
            samples_data = asdict(samples)

            redis_client.set(
                CACHE_KEY_SAMPLES,
                json.dumps(samples_data),
                ex=CACHE_TTL
            )

            return paginated_response(
                items=samples_data.get("samples"),
                page=samples_data.get("page", 1),
                per_page=samples_data.get("per_page", 12),
                total=samples_data.get("total")
            )
        except Exception as e:
            logger.error(f'Error fetching samples: {str(e)}')
            return error_response(
                'Failed to fetch samples',
                status=500
            )
            

class SampleDetailView(MethodView):
    def get(self, slug: str) -> tuple[Any, int]:
        try:
            cached_data = redis_client.get(f'sample:{slug}')
            if cached_data:
                data = json.loads(cached_data)
                logger.info(f'Sample fetched from cache: {slug}')
                return success_response(data)
            
            sample_data = get_services().sample.get_sample_by_slug(slug)
            sample_data = asdict(sample_data)

            redis_client.set(
                f'sample:{slug}',
                json.dumps(sample_data),
                ex=CACHE_TTL
            )

            return success_response(sample_data)
        except Exception as e:
            logger.error(f'Error fetching sample: {str(e)}')
            return error_response(
                'Failed to fetch sample',
                status=500
            )

class SampleServiceView(MethodView):
    def get(self) -> tuple[Any, int]:
        try:
            services = get_services().sample.get_sample_services()
            services_data = [asdict(s) for s in services]
            return success_response(services_data)
        except Exception as e:
            logger.error(f'Error fetching sample services: {str(e)}')
            return error_response(
                'Failed to fetch sample services',
                status=500
            )

class SampleRelatedView(MethodView):
    def get(self, slug: str) -> tuple[Any, int]:
        try:
            cached_data = redis_client.get(f'sample:{slug}:related')
            if cached_data:
                data = json.loads(cached_data)
                logger.info(f'Sample related fetched from cache: {slug}')
                return success_response(data)
            
            related_samples = get_services().sample.get_related(slug)
            related_samples_data = [asdict(s) for s in related_samples]

            redis_client.set(
                f'sample:{slug}:related',
                json.dumps(related_samples_data),
                ex=CACHE_TTL
            )

            return success_response(related_samples_data)
        except Exception as e:
            logger.error(f'Error fetching related samples: {str(e)}')
            return error_response(
                'Failed to fetch related samples',
                status=500
            )