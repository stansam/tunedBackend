from flask.views import MethodView
from tuned.interface import Services
from tuned.utils.responses import success_response, error_response
from tuned.redis_client import redis_client
from tuned.dtos import AcademicLevelResponseDTO

from dataclasses import asdict
import json
import logging

logger = logging.getLogger(__name__)

CACHE_TTL = 300
CACHE_KEY_ACADEMIC_LEVELS = 'academic_levels:list'


class GetAcademicLevels(MethodView):
    def get(self):
        try:
            cached = redis_client.get(CACHE_KEY_ACADEMIC_LEVELS)
            if cached:
                return success_response(
                    json.loads(cached),
                    "Academic levels fetched successfully"
                )
            
            interface = Services()
            academic_levels = interface.academic_level.list_academic_levels()
            academic_levels = [asdict(academic_level) for academic_level in academic_levels]
            
            redis_client.setex(
                CACHE_KEY_ACADEMIC_LEVELS, CACHE_TTL,
                json.dumps(academic_levels)
            )

            levels = []
            for a in academic_levels:
                data = f"{a["id"]} {a["name"]}, {a["order"]}"
                levels.append(data)
            print(level for level in levels)
            return success_response(
                academic_levels,
                "Academic levels fetched successfully"
            )

        except Exception as e:
            logger.error(f"Error fetching academic levels: {str(e)}")
            return error_response("Error fetching academic levels", str(e), 500)

# class GetContentTypes(MethodView):
#     def get(self):
#         try:
#             cached = redis_client.get('content_types')
#             if cached:
#                 return success_response(json.loads(cached), "Content types fetched successfully")
            
#             interface = Services()
#             content_types = interface.content_type.list_content_types()

#             redis_client.setex(
#                 'content_types', CACHE_TTL,
#                 json.dumps(asdict(content_types))
#             )
#             return success_response(asdict(content_types), "Content types fetched successfully")

#         except Exception as e:
#             logger.error(f"Error fetching content types: {str(e)}")
#             return error_response("Error fetching content types", str(e), 500)