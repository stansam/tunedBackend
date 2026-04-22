from flask.views import MethodView
from tuned.models.tag import Tag
from tuned.dtos.content import TagResponseDTO
from tuned.utils.responses import success_response, error_response
from tuned.core.logging import get_logger
from tuned.redis_client import redis_client
from dataclasses import asdict
import json
import logging

logger: logging.Logger = get_logger(__name__)

CACHE_TTL = 300
CACHE_KEY_TAGS = 'tags:list'

class GetTagsList(MethodView):
    def get(self):
        try:
            cached = redis_client.get(CACHE_KEY_TAGS)
            if cached:
                return success_response(
                    json.loads(cached),
                    "Tags fetched successfully"
                )
            
            # Fetch tags ordered by usage
            tags = Tag.query.order_by(Tag.usage_count.desc()).limit(20).all()
            tag_dtos = [asdict(TagResponseDTO.from_model(tag)) for tag in tags]
            
            redis_client.setex(
                CACHE_KEY_TAGS, CACHE_TTL,
                json.dumps(tag_dtos)
            )

            return success_response(
                tag_dtos,
                "Tags fetched successfully"
            )

        except Exception as e:
            logger.error(f"Error fetching tags: {str(e)}")
            return error_response("Error fetching tags", str(e), 500)
