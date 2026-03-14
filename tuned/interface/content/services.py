import logging
from collections import defaultdict

from tuned.models import Service
from tuned.models import ServiceCategory
from tuned.dtos import ServiceDTO, ServiceCategoryDTO
from tuned.repository import repositories
from tuned.repository.exceptions import AlreadyExists, DatabaseError, NotFound

logger = logging.getLogger(__name__)


class ServiceService:
    """Service layer for Service business logic."""

    def __init__(self) -> None:
        self._repo = repositories.service

    def create_service(self, data: ServiceDTO) -> Service:
        """Create a new service.

        Raises:
            AlreadyExists: If a service with the same name or slug already exists.
            DatabaseError: On unexpected database failure.
        """
        logger.info("Creating service: %s", data.name)
        service = self._repo.create(data)
        logger.info("Service created: id=%s slug=%s", service.id, service.slug)
        return service

    def get_service(self, service_id: str) -> Service:
        """Retrieve a service by its ID.

        Raises:
            NotFound: If no service exists with the given ID.
            DatabaseError: On unexpected database failure.
        """
        return self._repo.get_by_id(service_id)

    def get_service_by_slug(self, slug: str) -> Service:
        """Retrieve a service by its URL slug.

        Raises:
            NotFound: If no service exists with the given slug.
            DatabaseError: On unexpected database failure.
        """
        return self._repo.get_by_slug(slug)

    def list_services(self, active_only: bool = True) -> list[Service]:
        """Return all services.

        Args:
            active_only: When True (default) only active services are returned.

        Raises:
            DatabaseError: On unexpected database failure.
        """
        return self._repo.get_all(active_only=active_only)

    def list_featured_services(self) -> list[Service]:
        """Return active, featured services.

        Raises:
            DatabaseError: On unexpected database failure.
        """
        return self._repo.get_featured()
    
    def list_services_by_category(self) -> dict[str, list[Service]]:
        """Return all services grouped by category.

        Raises:
            DatabaseError: On unexpected database failure.
        """
        services: list[Service] = self._repo.get_all(active_only=True)
        services_by_category: dict[str, list[Service]] = defaultdict(list)
        for service in services:
            services_by_category[service.category_id].append(service)
        return services_by_category

    def update_service(self, service_id: str, updates: dict) -> Service:
        """Update mutable fields of a service.

        Only whitelisted fields are applied to guard against mass-assignment.

        Raises:
            NotFound: If no service exists with the given ID.
            AlreadyExists: If the update would create a name or slug conflict.
            DatabaseError: On unexpected database failure.
        """
        allowed_fields = {"name", "description", "category_id", "featured",
                          "pricing_category_id", "slug", "is_active"}
        safe_updates = {k: v for k, v in updates.items() if k in allowed_fields}
        logger.info("Updating service id=%s fields=%s", service_id, list(safe_updates.keys()))
        service = self._repo.update(service_id, safe_updates)
        logger.info("Service updated: id=%s", service_id)
        return service

    def delete_service(self, service_id: str) -> None:
        """Permanently delete a service.

        Raises:
            NotFound: If no service exists with the given ID.
            DatabaseError: On unexpected database failure.
        """
        logger.info("Deleting service id=%s", service_id)
        self._repo.delete(service_id)
        logger.info("Service deleted: id=%s", service_id)


class ServiceCategoryService:
    """Service layer for ServiceCategory business logic."""

    def __init__(self) -> None:
        self._repo = repositories.service_category

    def create_category(self, data: ServiceCategoryDTO) -> ServiceCategory:
        """Create a new service category.

        Raises:
            AlreadyExists: If a category with the same name already exists.
            DatabaseError: On unexpected database failure.
        """
        logger.info("Creating service category: %s", data.name)
        category = self._repo.create(data)
        logger.info("Service category created: id=%s", category.id)
        return category

    def get_category(self, category_id: str) -> ServiceCategory:
        """Retrieve a service category by its ID.

        Raises:
            NotFound: If no category exists with the given ID.
            DatabaseError: On unexpected database failure.
        """
        return self._repo.get_by_id(category_id)

    def list_categories(self) -> list[ServiceCategory]:
        """Return all service categories ordered by their display order.

        Raises:
            DatabaseError: On unexpected database failure.
        """
        return self._repo.get_all()

    def update_category(self, category_id: str, updates: dict) -> ServiceCategory:
        """Update mutable fields of a service category.

        Only whitelisted fields are applied to guard against mass-assignment.

        Raises:
            NotFound: If no category exists with the given ID.
            AlreadyExists: If the update would create a name conflict.
            DatabaseError: On unexpected database failure.
        """
        allowed_fields = {"name", "description", "order"}
        safe_updates = {k: v for k, v in updates.items() if k in allowed_fields}
        logger.info("Updating service category id=%s fields=%s", category_id, list(safe_updates.keys()))
        category = self._repo.update(category_id, safe_updates)
        logger.info("Service category updated: id=%s", category_id)
        return category

    def delete_category(self, category_id: str) -> None:
        """Permanently delete a service category.

        Raises:
            NotFound: If no category exists with the given ID.
            DatabaseError: On unexpected database failure.
        """
        logger.info("Deleting service category id=%s", category_id)
        self._repo.delete(category_id)
        logger.info("Service category deleted: id=%s", category_id)
