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

CACHE_KEY = 'services:list'
CACHE_TTL = 300

class GetServicesList(MethodView):
    def get(self) -> tuple[Any, int]:
        try:
            raw = redis_client.get(CACHE_KEY)
            if raw is not None and isinstance(raw, (str, bytes, bytearray)):
                logger.info("Services fetched successfully from cache")
                return success_response(json.loads(raw), "Services fetched successfully")
                
            services = get_services().service.list_services()
            services_dict = [asdict(s) for s in services] 

            redis_client.setex(
                CACHE_KEY, CACHE_TTL,
                json.dumps(services_dict)
            )
            return success_response(services_dict, "Services fetched successfully")

        except Exception as e:
            logger.error(f"Error fetching services: {str(e)}")
            return error_response("Failed to fetch services", status=500)

class GetServiceCategoriesList(MethodView):
    def get(self) -> tuple[Any, int]:
        try:
            raw = redis_client.get(f'{CACHE_KEY}:categories')
            if raw is not None and isinstance(raw, (str, bytes, bytearray)):
                logger.info("Services categories fetched successfully from cache")
                return success_response(json.loads(raw), "Services categories fetched successfully")
            
            categories = get_services().service_category.list_categories()
            categories_dict = [asdict(c) for c in categories]
            redis_client.setex(
                f'{CACHE_KEY}:categories', CACHE_TTL,
                json.dumps(categories_dict)
            )

            logger.info("Services categories fetched successfully")
            return success_response(categories_dict, "Services categories fetched successfully")

        except Exception as e:
            logger.error(f"Error fetching services categories: {str(e)}")
            return error_response("Failed to fetch service categories", status=500)
            
class GetServicesByCategory(MethodView):
    def get(self, category_id: str) -> tuple[Any, int]:
        try:
            raw = redis_client.get(f'service:category:{category_id}:list')
            if raw is not None and isinstance(raw, (str, bytes, bytearray)):
                logger.info("Services fetched successfully from cache")
                return success_response(json.loads(raw), "Services fetched successfully")

            services = get_services().service.list_services_by_category(category_id)
            services_dict = [asdict(s) for s in services]

            redis_client.setex(
                f'service:category:{category_id}:list', CACHE_TTL,
                json.dumps(services_dict)
            )

            logger.info("Services fetched successfully")
            return success_response(services_dict, "Services fetched successfully")

        except Exception as e:
            logger.error(f"Error fetching services by category: {str(e)}")
            return error_response("Failed to fetch services by category", status=500)
            
class GetServicesBySlug(MethodView):
    def get(self, slug: str) -> tuple[Any, int]:
        try:
            raw = redis_client.get(f'service:{slug}')
            if raw is not None and isinstance(raw, (str, bytes, bytearray)):
                logger.info("Service fetched successfully from cache")
                return success_response(json.loads(raw), "Service fetched successfully")
            
            service = get_services().service.get_service_by_slug(slug)
            service_dict = asdict(service)
            

            redis_client.setex(
                f'service:{slug}', CACHE_TTL,
                json.dumps(service_dict)
            )

            logger.info("Service fetched successfully")
            return success_response(service_dict, "Service fetched successfully")

        except Exception as e:
            logger.error(f"Error fetching service by slug: {str(e)}")
            return error_response("Failed to fetch service details", status=500)

class GetServicesRelated(MethodView):
    def get(self, slug: str) -> tuple[Any, int]:
        try:
            raw = redis_client.get(f'service:{slug}:related')
            if raw is not None and isinstance(raw, (str, bytes, bytearray)):
                logger.info("Service related fetched successfully from cache")
                return success_response(json.loads(raw), "Service related fetched successfully")
            
            service = get_services().service.get_service_by_slug(slug)
            related_services = get_services().service.list_services_by_category(service.category_id)
            related_samples = get_services().sample.list_samples_by_service(service.id)

            related_services_dict = [asdict(s) for s in related_services]
            related_samples_dict = [asdict(s) for s in related_samples]

            data_items = {
                "services": related_services_dict,
                "samples": related_samples_dict,
            }
            
            redis_client.setex(
                f'service:{slug}:related', CACHE_TTL,
                json.dumps(data_items)
            )

            logger.info("Service related fetched successfully")
            return success_response(data_items, "Service related fetched successfully")

        except Exception as e:
            logger.error(f"Error fetching service related: {str(e)}")
            return error_response("Failed to fetch related content", status=500)