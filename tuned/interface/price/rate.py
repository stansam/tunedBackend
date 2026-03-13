import logging

from tuned.dtos import (
    PriceRateDTO,
    PriceRateResponseDTO,
    PriceRateLookupDTO,
)
from tuned.repository import Repository
from tuned.repository.exceptions import AlreadyExists, DatabaseError, NotFound

logger = logging.getLogger(__name__)


class PriceRateService:
    """Service layer for PriceRate business logic."""

    def __init__(self) -> None:
        self._repo = Repository.price_rate

    def create_rate(self, data: PriceRateDTO) -> PriceRateResponseDTO:
        """Create a new price rate.

        Raises:
            AlreadyExists: If a rate for this category/level/deadline triple already exists.
            DatabaseError: On unexpected database failure.
        """
        logger.info(
            "Creating price rate: category=%s level=%s deadline=%s price=%.2f",
            data.pricing_category_id,
            data.academic_level_id,
            data.deadline_id,
            data.price_per_page,
        )
        result = self._repo.create(data)
        logger.info("Price rate created: id=%s", result.id)
        return result

    def get_rate(self, rate_id: str) -> PriceRateResponseDTO:
        """Retrieve a price rate by ID.

        Raises:
            NotFound: If no rate exists with the given ID.
            DatabaseError: On unexpected database failure.
        """
        return self._repo.get_by_id(rate_id)

    def lookup_rate(self, lookup: PriceRateLookupDTO) -> PriceRateResponseDTO:
        """Resolve the active rate for a specific category/academic-level/deadline combination.

        This is the primary query used during order pricing.

        Raises:
            NotFound: If no active rate exists for the given combination.
            DatabaseError: On unexpected database failure.
        """
        return self._repo.get_by_dimensions(lookup)

    def list_rates_by_category(
        self, pricing_category_id: str, active_only: bool = True
    ) -> list[PriceRateResponseDTO]:
        """Return all rates for a given pricing category.

        Raises:
            DatabaseError: On unexpected database failure.
        """
        return self._repo.get_by_category(pricing_category_id, active_only)

    def update_rate(self, rate_id: str, updates: dict) -> PriceRateResponseDTO:
        """Update mutable fields of a price rate.

        Raises:
            NotFound: If no rate exists with the given ID.
            AlreadyExists: If the update would violate the unique constraint.
            DatabaseError: On unexpected database failure.
        """
        allowed = {"price_per_page", "is_active"}
        safe_updates = {k: v for k, v in updates.items() if k in allowed}
        logger.info("Updating price rate id=%s fields=%s", rate_id, list(safe_updates.keys()))
        result = self._repo.update(rate_id, safe_updates)
        logger.info("Price rate updated: id=%s", rate_id)
        return result

    def delete_rate(self, rate_id: str) -> None:
        """Permanently delete a price rate.

        Raises:
            NotFound: If no rate exists with the given ID.
            DatabaseError: On unexpected database failure.
        """
        logger.info("Deleting price rate id=%s", rate_id)
        self._repo.delete(rate_id)
        logger.info("Price rate deleted: id=%s", rate_id)
