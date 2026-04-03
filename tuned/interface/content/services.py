import logging
from collections import defaultdict
from tuned.dtos import(
    ServiceDTO, ServiceResponseDTO
)
from tuned.repository import repositories
from tuned.repository.exceptions import AlreadyExists, DatabaseError, NotFound
from tuned.core.logging import get_logger

logger: logging.Logger = get_logger(__name__)

class ServiceService:
    def __init__(self) -> None:
        self._repo = repositories.service

    def create_service(self, data: ServiceDTO) -> ServiceResponseDTO:
        try:
            logger.info("Creating service: %s", data.name)
            service = self._repo.create(data)
            logger.info("Service created: id=%s slug=%s", service.id, service.slug)
            return service
        except AlreadyExists:
            logger.error("service already exists")
            raise AlreadyExists("service already exists")
        except DatabaseError:
            logger.error("Database error while creating service")
            raise DatabaseError("Database error while creating service")

    def get_service(self, service_id: str) -> ServiceResponseDTO:
        try:
            return self._repo.get_by_id(service_id)
        except NotFound:
            logger.error("service not found: %s", service_id)
            raise NotFound("service not found")
        except DatabaseError:
            logger.error("Database error while fetching service")
            raise DatabaseError("Database error while fetching service")

    def get_service_by_slug(self, slug: str) -> ServiceResponseDTO:
        try:
            return self._repo.get_by_slug(slug)
        except NotFound:
            logger.error("service not found: %s", slug)
            raise NotFound("service not found")
        except DatabaseError:
            logger.error("Database error while fetching service")
            raise DatabaseError("Database error while fetching service")

    def list_services(self, active_only: bool = True) -> list[ServiceResponseDTO]:
        try:
            return self._repo.get_all(active_only=active_only)
        except NotFound:
            logger.error("services not found")
            raise NotFound("services not found")
        except DatabaseError:
            logger.error("Database error while fetching services")
            raise DatabaseError("Database error while fetching services")

    def list_featured_services(self) -> list[ServiceResponseDTO]:
        try:
            return self._repo.get_featured()
        except NotFound:
            logger.error("services not found")
            raise NotFound("services not found")
        except DatabaseError:
            logger.error("Database error while fetching services")
            raise DatabaseError("Database error while fetching services")
    
    def list_services_by_category(self) -> dict[str, list[ServiceResponseDTO]]:
        try:
            services: list[ServiceResponseDTO] = self._repo.get_all(active_only=True)
            services_by_category: dict[str, list[ServiceResponseDTO]] = defaultdict(list)
            for service in services:
                services_by_category[service.category_id].append(service)
            return services_by_category
        except NotFound:
            logger.error("services not found")
            raise NotFound("services not found")
        except DatabaseError:
            logger.error("Database error while fetching services")
            raise DatabaseError("Database error while fetching services")

    def update_service(self, service_id: str, updates: dict) -> ServiceResponseDTO:
        try:
            allowed_fields = {"name", "description", "category_id", "featured",
                            "pricing_category_id", "slug", "is_active"}
            safe_updates = {k: v for k, v in updates.items() if k in allowed_fields}
            logger.info("Updating service id=%s fields=%s", service_id, list(safe_updates.keys()))
            service = self._repo.update(service_id, safe_updates)
            logger.info("Service updated: id=%s", service_id)
            return service
        except NotFound:
            logger.error("service not found: %s", service_id)
            raise NotFound("service not found")
        except DatabaseError:
            logger.error("Database error while updating service")
            raise DatabaseError("Database error while updating service")

    def delete_service(self, service_id: str) -> None:
        logger.info("Deleting service id=%s", service_id)
        self._repo.delete(service_id)
        logger.info("Service deleted: id=%s", service_id)
    
    def get_services_by_category(self, category_id: str) -> list[ServiceResponseDTO]:
        try:
            return self._repo.get_services_by_category(category_id)
        except NotFound:
            logger.error("services not found: %s", category_id)
            raise NotFound("services not found")
        except DatabaseError:
            logger.error("Database error while fetching services")
            raise DatabaseError("Database error while fetching services")