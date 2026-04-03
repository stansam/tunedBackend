from flask import request
from flask.views import MethodView
from tuned.interface import Services
from tuned.utils.responses import error_response, success_response
from tuned.redis_client import redis_client
from tuned.core.logging import get_logger

from dataclasses import asdict
import json
import logging

logger: logging.Logger = get_logger(__name__)


CACHE_KEY: str = "blog:categories"
CACHE_TTL: int = 60 * 60 * 24

class ListBlogCategories(MethodView):
    def __init__(self):
        self._interface = Services()

    def get(self):
        try:
            cached_data = redis_client.get(CACHE_KEY)
            if cached_data:
                logger.debug('Returning blog categories from cache')
                return success_response(cached_data)
            
            categories = self._interface.blog_category.list_categories()
            categories = [asdict(category) for category in categories]
            
            redis_client.set(
                CACHE_KEY,
                json.dumps(categories),
                ex=CACHE_TTL
                )
            
            return success_response(categories)
        except Exception as e:
            logger.error(f'Error fetching blog categories: {str(e)}')
            return error_response(
                'Failed to fetch blog categories',
                status=500
            )
            
            
            
                    
            
        
    