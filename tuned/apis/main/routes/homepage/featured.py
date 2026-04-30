from flask.views import MethodView
from tuned.utils.dependencies import get_services
from tuned.utils.responses import success_response, error_response
from tuned.redis_client import redis_client
from tuned.core.logging import get_logger

from dataclasses import asdict
import json
import logging
from typing import Any

logger: logging.Logger = get_logger(__name__)

CACHE_KEY = 'homepage:featured'
CACHE_TTL = 300

class GetFeaturedContent(MethodView): 
    def get(self) -> tuple[Any, int]:
        try:
            cached_data = redis_client.get(CACHE_KEY)
            if cached_data:
                logger.debug('Returning featured content from cache')
                return success_response(json.loads(cached_data))
            
            # TODO: Implement strict response DTOs
            featured_services = get_services().service_category.list_categories()
            featured_samples = get_services().sample.list_featured_samples()
            featured_blogs = get_services().blogs.post.list_featured()
            data = {
                'services': [asdict(s) for s in featured_services],
                'samples': [asdict(s) for s in featured_samples],
                'blogs': [asdict(b) for b in featured_blogs]
            }

            redis_client.setex(
                CACHE_KEY,
                CACHE_TTL,
                json.dumps(data)
            )
            
            return success_response(data)
        except Exception as e:
            logger.error(f'Error fetching featured content: {str(e)}')
            return error_response(
                'Failed to fetch featured content',
                status=500
            )
