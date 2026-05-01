from flask import request
from flask.views import MethodView
from marshmallow import ValidationError
from dataclasses import asdict
import logging
from typing import Any

from tuned.utils.dependencies import get_services
from tuned.apis.main.schemas import SearchQuerySchema
from tuned.utils.responses import (
    success_response, 
    validation_error_response,
    error_response
)
from tuned.core.logging import get_logger

logger: logging.Logger = get_logger(__name__)

class GlobalSearchView(MethodView):
    def __init__(self) -> None:
        self._schema = SearchQuerySchema()

    def get(self) -> tuple[Any, int]:
        try:
            params = self._schema.load(request.args)
            
            query = params['q']
            search_type = params.get('type', 'all')
            page = params.get('page', 1)
            per_page = params.get('per_page', 20)
            
            search_dto = get_services().search.global_search(
                query=query,
                search_type=search_type,
                page=page,
                per_page=per_page
            )
            
            return success_response(asdict(search_dto))
            
        except ValidationError as err:
            return validation_error_response(err.messages)
        except Exception as e:
            logger.error(f'Error performing search: {str(e)}')
            return error_response('Failed to perform search', status=500)
