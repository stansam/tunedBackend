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

CACHE_KEY = 'blogs:comments'
CACHE_TTL = 300

class GetBlogComments(MethodView):
    def get(self, blog_id: int) -> tuple[Any, int]:
        try:
            raw = redis_client.get(f'{CACHE_KEY}:{blog_id}')
            if raw is not None and isinstance(raw, (str, bytes, bytearray)):
                logger.debug('Returning comments from cache')
                return success_response(json.loads(raw))
            
            comments = get_services().blogs.comment.get_blog_comments(blog_id)
            data = {
                'comments': [asdict(c) for c in comments]
            }

            redis_client.setex(
                f'{CACHE_KEY}:{blog_id}',
                CACHE_TTL,
                json.dumps(data)
            )
            
            return success_response(data)
        except Exception as e:
            logger.error(f'Error fetching comments: {str(e)}')
            return error_response('Failed to fetch comments', status=500)
