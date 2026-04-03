from tuned.core.logging import get_logger
from flask.views import MethodView
from tuned.interface import service as _interface, blog_category as _category_interface, sample as _samples_interface
from tuned.utils.responses import success_response, error_response
from tuned.redis_client import redis_client


from dataclasses import asdict
import json
import logging

logger: logging.Logger = get_logger(__name__)

CACHE_KEY = 'services:list'
CACHE_TTL = 300

class GetServicesList(MethodView):
    def get(self):
        try:
            cached = redis_client.get(CACHE_KEY)
            if cached:
                return success_response(json.loads(cached), "Services fetched successfully")
            services = _interface.list_services()

            redis_client.setex(
                CACHE_KEY, CACHE_TTL,
                json.dumps(asdict(services))
            )
            return success_response("Services fetched successfully", asdict(services))

        except Exception as e:
            logger.error(f"Error fetching services: {str(e)}")
            return error_response("Error fetching services", str(e), 500)

class GetServiceCategoriesList(MethodView):
    def get(self):
        try:
            cached = redis_client.get(CACHE_KEY)
            if cached:
                return success_response("Services categories fetched successfully", json.loads(cached))
            
            categories = _category_interface.list_categories()
            categories = [asdict(c) for c in categories]
            redis_client.setex(
                CACHE_KEY, CACHE_TTL,
                json.dumps(categories)
            )
            return success_response(categories, "Services categories fetched successfully")

        except Exception as e:
            logger.error(f"Error fetching services categories: {str(e)}")
            return error_response("Error fetching services categories", str(e), 500)
            
class GetServicesByCategory(MethodView):
    def get(self, category_id):
        try:
            cached = redis_client.get(f'service:category:{category_id}')
            if cached:
                return success_response(json.loads(cached), "Services fetched successfully")

            services = _interface.get_services_by_category(category_id)
            services = [asdict(s) for s in services]

            redis_client.setex(
                f'service:category:{category_id}', CACHE_TTL,
                json.dumps(services)
            )

            return success_response(services, "Services fetched successfully")

        except Exception as e:
            logger.error(f"Error fetching services by category: {str(e)}")
            return error_response("Error fetching services by category", str(e), 500)
            
class GetServicesBySlug(MethodView):
    def get(self, slug):
        try:
            cached = redis_client.get(f'service:{slug}')
            if cached:
                return success_response(json.loads(cached), "Service fetched successfully")
            
            service = _interface.get_service_by_slug(slug)
            service = asdict(service)
            

            redis_client.setex(
                f'service:{slug}', CACHE_TTL,
                json.dumps(service)
            )
            return success_response(service, "Service fetched successfully")

        except Exception as e:
            logger.error(f"Error fetching service by slug: {str(e)}")
            return error_response("Error fetching service by slug", str(e), 500)

class GetServicesRelated(MethodView):
    def get(self, slug):
        try:
            cached = redis_client.get(f'service:{slug}:related')
            if cached:
                return success_response(json.loads(cached), "Service related fetched successfully")
            
            service = _interface.get_service_by_slug(slug)
            related_services = _interface.get_services_by_category(service.category_id)
            related_samples = _samples_interface.get_samples_by_service_id(service.id)

            related_services = [asdict(s) for s in related_services]
            related_samples = [asdict(s) for s in related_samples]

            data_items = {
                "services": related_services,
                "samples": related_samples,
            }
            
            redis_client.setex(
                f'service:{slug}:related', CACHE_TTL,
                json.dumps(data_items)
            )

            return success_response(asdict(data_items), "Service related fetched successfully")

        except Exception as e:
            logger.error(f"Error fetching service related: {str(e)}")
            return error_response("Error fetching service related", str(e), 500)