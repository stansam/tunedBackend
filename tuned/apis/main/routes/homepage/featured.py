"""
Homepage featured content endpoint.

GET /api/featured - Fetch featured services, samples, and blog posts
"""
from flask.views import MethodView
from tuned.interface import Services
from tuned.utils.responses import success_response, error_response
from tuned.redis_client import redis_client

from dataclasses import asdict
import json
import logging

logger = logging.getLogger(__name__)

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
            featured_services = self._interface.pricing_category.list_categories()
            featured_samples = self._interface.sample.list_featured_samples()
            featured_blogs = self._interface.blog.list_featured_blogs()
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
