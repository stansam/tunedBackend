import logging

from tuned.dtos import (
    PricingCategoryDTO,
    PricingCategoryResponseDTO,
)
from tuned.repository import Repository
from tuned.repository.exceptions import AlreadyExists, DatabaseError, NotFound

logger = logging.getLogger(__name__)


class PricingCategoryService:
    """Service layer for PricingCategory business logic."""

    def __init__(self) -> None:
        self._repo = Repository.pricing_category

    def create_category(self, data: PricingCategoryDTO) -> PricingCategoryResponseDTO:
        """Create a new pricing category.

        Raises:
            AlreadyExists: If a category with this name already exists.
            DatabaseError: On unexpected database failure.
        """
        logger.info("Creating pricing category: %s", data.name)
        result = self._repo.create(data)
        logger.info("Pricing category created: id=%s", result.id)
        return result

    def get_category(self, category_id: str) -> PricingCategoryResponseDTO:
        """Retrieve a pricing category by ID.

        Raises:
            NotFound: If no category exists with the given ID.
            DatabaseError: On unexpected database failure.
        """
        return self._repo.get_by_id(category_id)

    def list_categories(self) -> list[PricingCategoryResponseDTO]:
        """Return all pricing categories ordered by display_order.

        Raises:
            DatabaseError: On unexpected database failure.
        """
        return self._repo.get_all()

    def update_category(self, category_id: str, updates: dict) -> PricingCategoryResponseDTO:
        """Update mutable fields of a pricing category.

        Raises:
            NotFound: If no category exists with the given ID.
            AlreadyExists: If the update would cause a name conflict.
            DatabaseError: On unexpected database failure.
        """
        allowed = {"name", "description", "display_order"}
        safe_updates = {k: v for k, v in updates.items() if k in allowed}
        logger.info("Updating pricing category id=%s fields=%s", category_id, list(safe_updates.keys()))
        result = self._repo.update(category_id, safe_updates)
        logger.info("Pricing category updated: id=%s", category_id)
        return result

    def delete_category(self, category_id: str) -> None:
        """Permanently delete a pricing category.

        Raises:
            NotFound: If no category exists with the given ID.
            DatabaseError: On unexpected database failure.
        """
        logger.info("Deleting pricing category id=%s", category_id)
        self._repo.delete(category_id)
        logger.info("Pricing category deleted: id=%s", category_id)
