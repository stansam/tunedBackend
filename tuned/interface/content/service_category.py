import logging

from tuned.models import ServiceCategory
from tuned.dtos import(
    ServiceCategoryDTO, ServiceCategoryResponseDTO
)
from tuned.repository import repositories
from tuned.repository.exceptions import AlreadyExists, DatabaseError, NotFound
from tuned.core.logging import get_logger

logger: logging.Logger = get_logger(__name__)

class ServiceCategoryService:
    def __init__(self) -> None:
        self._repo = repositories.service_category

    def create_category(self, data: ServiceCategoryDTO) -> ServiceCategoryResponseDTO:
        try:
            logger.info("Creating service category: %s", data.name)
            category = self._repo.create(data)
            logger.info("Service category created: id=%s", category.id)
            return category
        except AlreadyExists:
            logger.error("category already exists")
            raise AlreadyExists("category already exists")
        except DatabaseError:
            logger.error("Database error while creating category")
            raise DatabaseError("Database error while creating category")

    def get_category(self, category_id: str) -> ServiceCategoryResponseDTO:
        try:
            logger.debug("Fetching category: %s", category_id)
            return self._repo.get_by_id(category_id)
        except NotFound:
            logger.error("category not found: %s", category_id)
            raise NotFound("category not found")
        except DatabaseError:
            logger.error("Database error while fetching category")
            raise DatabaseError("Database error while fetching category")

    def list_categories(self) -> list[ServiceCategory]:
        try:
            logger.debug("Fetching all categories")
            return self._repo.get_all()
        except DatabaseError:
            logger.error("Database error while fetching categories")
            raise DatabaseError("Database error while fetching categories")

    def update_category(self, category_id: str, updates: dict) -> ServiceCategoryResponseDTO:
        try:
            allowed_fields = {"name", "description", "order"}
            safe_updates = {k: v for k, v in updates.items() if k in allowed_fields}
            logger.info("Updating service category id=%s fields=%s", category_id, list(safe_updates.keys()))
            category = self._repo.update(category_id, safe_updates)
            logger.info("Service category updated: id=%s", category_id)
            return category
        except NotFound:
            logger.error("category not found: %s", category_id)
            raise NotFound("category not found")
        except DatabaseError:
            logger.error("Database error while updating or deleting category")
            raise DatabaseError("Database error while updating or deleting category")

    def delete_category(self, category_id: str) -> None:
        logger.info("Deleting service category id=%s", category_id)
        self._repo.delete(category_id)
        logger.info("Service category deleted: id=%s", category_id)
