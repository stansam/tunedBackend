from flask import request
from flask.views import MethodView
from tuned.interface import blog_post as _interface
from tuned.utils.responses import paginated_response, error_response, validation_error_response, success_response
from tuned.redis_client import redis_client
from tuned.apis.main.schemas import BlogFilterSchema
from tuned.dtos import BlogPostListRequestDTO
from tuned.core.logging import get_logger
from marshmallow import ValidationError

from dataclasses import asdict
import json
import logging

logger: logging.Logger = get_logger(__name__)

CACHE_KEY = 'blogs:all'
CACHE_TTL = 300

class ListBlogPosts(MethodView):
    def __init__(self):
        self._schema = BlogFilterSchema()

    def get(self):
        try:
            params = {}
            if request.args:
                params = self._schema.load(request.args)
            
        except ValidationError as err:
            logger.error(f'Validation error: {str(err)}')
            return validation_error_response(err.messages)

        try:
            cache_key = f'{CACHE_KEY}:{json.dumps(params)}'
            cached_data = redis_client.get(cache_key)
            if cached_data:
                logger.debug('Returning blogs from cache')
                data = json.loads(cached_data)
                return paginated_response(
                    items=data.get("blogs"),
                    page=data.get("page", 1),
                    per_page=data.get("per_page", 12),
                    total=data.get("total")
                    )
            req = BlogPostListRequestDTO(**params)
            blogs = _interface.list_published(req)
            data = asdict(blogs)

            redis_client.setex(
                cache_key,
                CACHE_TTL,
                json.dumps(data)
            )
            
            return paginated_response(
                items=data.get("blogs"),
                page=data.get("page", 1),
                per_page=data.get("per_page", 12),
                total=data.get("total")
                )
        except Exception as e:
            logger.error(f'Error fetching blogs: {str(e)}')
            return error_response(
                'Failed to fetch blogs',
                status=500
            )

class GetBlogPost(MethodView):

    def get(self, slug):
        try:
            cached_data = redis_client.get(f'blog:{slug}')
            if cached_data:
                logger.debug('Returning blog from cache')
                return success_response(json.loads(cached_data))
            
            blog = _interface.get_by_slug(slug)
            data = {
                'blog': asdict(blog)
            }

            redis_client.setex(
                f'blog:{slug}',
                CACHE_TTL,
                json.dumps(data)
            )
            
            return success_response(data)
        except Exception as e:
            logger.error(f'Error fetching blog: {str(e)}')
            return error_response(
                'Failed to fetch blog',
                status=500
            )