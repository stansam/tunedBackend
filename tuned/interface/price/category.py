from __future__ import annotations
import logging
from typing import Optional, TYPE_CHECKING
from tuned.dtos import (
    PricingCategoryDTO,
    PricingCategoryResponseDTO,
)
from tuned.repository.exceptions import AlreadyExists, DatabaseError, NotFound
from tuned.core.logging import get_logger

if TYPE_CHECKING:
    from tuned.repository import Repository

logger: logging.Logger = get_logger(__name__)

class PricingCategoryService:
    def __init__(self, repos: Optional[Repository] = None) -> None:
        if repos:
            self._repo = repos.pricing_category
        else:
            from tuned.repository import repositories
            self._repo = repositories.pricing_category

    def create_category(self, data: PricingCategoryDTO) -> PricingCategoryResponseDTO:
        try:
            logger.info("Creating pricing category: %s", data.name)
            result = self._repo.create(data)
            logger.info("Pricing category created: id=%s", result.id)
            return result
        except AlreadyExists:
            logger.error("Pricing category already exists: %s", data.name)
            raise AlreadyExists("Pricing category already exists")
        except DatabaseError:
            logger.error("Database error while creating pricing category")
            raise DatabaseError("Database error while creating pricing category")

    def get_category(self, category_id: str) -> PricingCategoryResponseDTO:
        try:
            return self._repo.get_by_id(category_id)
        except NotFound:
            logger.error("Pricing category not found: %s", category_id)
            raise NotFound("Pricing category not found")
        except DatabaseError:
            logger.error("Database error while fetching pricing category")
            raise DatabaseError("Database error while fetching pricing category")

    def list_categories(self) -> list[PricingCategoryResponseDTO]:
        try:
            return self._repo.get_all()
        except DatabaseError:
            logger.error("Database error while fetching pricing categories")
            raise DatabaseError("Database error while fetching pricing categories")

    def update_category(self, category_id: str, updates: dict) -> PricingCategoryResponseDTO:
        try:
            allowed = {"name", "description", "display_order"}
            safe_updates = {k: v for k, v in updates.items() if k in allowed}
            logger.info("Updating pricing category id=%s fields=%s", category_id, list(safe_updates.keys()))
            result = self._repo.update(category_id, safe_updates)
            logger.info("Pricing category updated: id=%s", category_id)
            return result
        except NotFound:
            logger.error("Pricing category not found: %s", category_id)
            raise NotFound("Pricing category not found")
        except DatabaseError:
            logger.error("Database error while updating pricing category")
            raise DatabaseError("Database error while updating pricing category")

    def delete_category(self, category_id: str) -> None:
        try:
            logger.info("Deleting pricing category id=%s", category_id)
            self._repo.delete(category_id)
            logger.info("Pricing category deleted: id=%s", category_id)
        except NotFound:
            logger.error("Pricing category not found: %s", category_id)
            raise NotFound("Pricing category not found")
        except DatabaseError:
            logger.error("Database error while deleting pricing category")
            raise DatabaseError("Database error while deleting pricing category")
