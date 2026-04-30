from __future__ import annotations
import logging
from typing import Optional, TYPE_CHECKING

from tuned.dtos import ServiceCategoryDTO, ServiceCategoryResponseDTO
from tuned.repository.exceptions import AlreadyExists, DatabaseError, NotFound
from tuned.core.logging import get_logger

if TYPE_CHECKING:
    from tuned.repository import Repository

logger: logging.Logger = get_logger(__name__)


class ServiceCategoryService:
    """Service layer for service category business logic."""

    def __init__(self, repos: Optional[Repository] = None) -> None:
        if repos:
            self._repo = repos.service_category
        else:
            from tuned.repository import repositories
            self._repo = repositories.service_category

    def create_category(self, data: ServiceCategoryDTO) -> ServiceCategoryResponseDTO:
        try:
            logger.info("Creating service category: %s", data.name)
            result = self._repo.create(data)
            logger.info("Service category created: id=%s", result.id)
            return result
        except AlreadyExists:
            logger.error("Service category already exists: %s", data.name)
            raise AlreadyExists("Service category already exists")
        except DatabaseError:
            logger.error("Database error while creating service category")
            raise DatabaseError("Database error while creating service category")

    def get_category(self, category_id: str) -> ServiceCategoryResponseDTO:
        try:
            return self._repo.get_by_id(category_id)
        except NotFound:
            logger.error("Service category not found: %s", category_id)
            raise NotFound("Service category not found")
        except DatabaseError:
            logger.error("Database error while fetching service category")
            raise DatabaseError("Database error while fetching service category")

    def list_categories(self) -> list[ServiceCategoryResponseDTO]:
        try:
            return self._repo.get_all()
        except DatabaseError:
            logger.error("Database error while fetching service categories")
            raise DatabaseError("Database error while fetching service categories")

    def update_category(self, category_id: str, updates: dict) -> ServiceCategoryResponseDTO:
        try:
            allowed = {"name", "description", "icon_url", "display_order"}
            safe_updates = {k: v for k, v in updates.items() if k in allowed}
            logger.info("Updating service category id=%s fields=%s", category_id, list(safe_updates.keys()))
            result = self._repo.update(category_id, safe_updates)
            logger.info("Service category updated: id=%s", category_id)
            return result
        except NotFound:
            logger.error("Service category not found: %s", category_id)
            raise NotFound("Service category not found")
        except DatabaseError:
            logger.error("Database error while updating service category")
            raise DatabaseError("Database error while updating service category")

    def delete_category(self, category_id: str) -> None:
        try:
            logger.info("Deleting service category id=%s", category_id)
            self._repo.delete(category_id)
            logger.info("Service category deleted: id=%s", category_id)
        except NotFound:
            logger.error("Service category not found: %s", category_id)
            raise NotFound("Service category not found")
        except DatabaseError:
            logger.error("Database error while deleting service category")
            raise DatabaseError("Database error while deleting service category")
