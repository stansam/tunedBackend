from tuned.core.logging import get_logger
from flask.views import MethodView
from tuned.utils.dependencies import get_services
from tuned.utils.responses import success_response, error_response
from tuned.redis_client import redis_client

from dataclasses import asdict
import json
import logging
from typing import Any

logger: logging.Logger = get_logger(__name__)

CACHE_TTL = 300
CACHE_KEY_ACADEMIC_LEVELS = 'academic_levels:list'


class GetAcademicLevels(MethodView):
    def get(self) -> tuple[Any, int]:
        try:
            cached = redis_client.get(CACHE_KEY_ACADEMIC_LEVELS)
            if cached:
                return success_response(
                    json.loads(cached),
                    "Academic levels fetched successfully"
                )
            
            academic_levels = get_services().academic_level.list_academic_levels()
            academic_levels = [asdict(academic_level) for academic_level in academic_levels]
            
            redis_client.setex(
                CACHE_KEY_ACADEMIC_LEVELS, CACHE_TTL,
                json.dumps(academic_levels)
            )

            return success_response(
                academic_levels,
                "Academic levels fetched successfully"
            )

        except Exception as e:
            logger.error(f"Error fetching academic levels: {str(e)}")
            return error_response("Error fetching academic levels", str(e), 500)
