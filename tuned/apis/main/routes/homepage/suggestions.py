from flask import request
from flask.views import MethodView
from marshmallow import ValidationError
from typing import Any
from tuned.apis.main.schemas.homepage import SuggestionsQuerySchema
from tuned.utils.dependencies import get_services
from tuned.utils.responses import (
    success_response, 
    validation_error_response,
    error_response
)
from tuned.core.logging import get_logger

logger = get_logger(__name__)

class GetSearchSuggestions(MethodView):
    def __init__(self) -> None:
        self._schema = SuggestionsQuerySchema()

    def get(self) -> tuple[Any, int]:
        try:
            params = self._schema.load(request.args)
            query = params['q']
            
            clean_query = query.strip()
            escaped_query = clean_query.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')
            search_pattern = f"%{escaped_query}%"
            
            services = get_services().search._repos.search.search_services(search_pattern, offset=0, limit=3)
            samples = get_services().search._repos.search.search_samples(search_pattern, offset=0, limit=3)
            blogs = get_services().search._repos.search.search_blogs(search_pattern, offset=0, limit=3)
            tags = get_services().search._repos.search.search_tags(search_pattern, offset=0, limit=3)
            
            response_data = {
                "services": [{"id": str(s.id), "name": s.name, "slug": s.slug} for s in services],
                "samples": [{"id": str(s.id), "title": s.title, "slug": s.slug} for s in samples],
                "blogs": [{"id": str(b.id), "title": b.title, "slug": b.slug} for b in blogs],
                "tags": [{"id": str(t.id), "name": t.name, "slug": t.slug} for t in tags]
            }
            
            return success_response(response_data, "Suggestions fetched successfully")
            
        except ValidationError as err:
            return validation_error_response(err.messages)
        except Exception as e:
            logger.error(f'Error getting suggestions: {str(e)}')
            return error_response('Failed to fetch suggestions', status=500)
