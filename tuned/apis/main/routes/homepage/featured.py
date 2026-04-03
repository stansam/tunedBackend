from flask.views import MethodView
from tuned.interface import service as _service_interface, sample as _sample_interface, blog_post as _blog_interface
from tuned.utils.responses import success_response, error_response
from tuned.redis_client import redis_client
from tuned.core.logging import get_logger

from dataclasses import asdict
import json
import logging

logger: logging.Logger = get_logger(__name__)

CACHE_KEY = 'homepage:featured'
CACHE_TTL = 300

class GetFeaturedContent(MethodView): #TODO: Implement strict return types 
    def __init__(self):
        self._interface = Services()

    def get(self):
        try:
            cached_data = redis_client.get(CACHE_KEY)
            if cached_data:
                logger.debug('Returning featured content from cache')
                return success_response(json.loads(cached_data))
            
            # TODO: Implement strict response DTOs
            featured_services = _service_interface.list_categories()
            featured_samples = _sample_interface.list_featured_samples()
            featured_blogs = _blog_interface.list_featured()
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
