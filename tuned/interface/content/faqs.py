import logging

from tuned.dtos import FaqDTO, FaqResponseDTO
from tuned.repository import Repository
from tuned.repository.exceptions import AlreadyExists, DatabaseError, NotFound

logger = logging.getLogger(__name__)


class FAQService:
    """Service layer for FAQ business logic."""

    def __init__(self) -> None:
        self._repo = Repository.faq

    def create_faq(self, data: FaqDTO) -> FaqResponseDTO:
        """Create a new FAQ entry.

        Raises:
            AlreadyExists: If a FAQ with this question already exists.
            DatabaseError: On unexpected database failure.
        """
        logger.info("Creating FAQ in category '%s'", data.category)
        result = self._repo.create(data)
        logger.info("FAQ created: id=%s", result.id)
        return result

    def get_faq(self, faq_id: str) -> FaqResponseDTO:
        """Retrieve a FAQ by ID.

        Raises:
            NotFound: If no FAQ exists with the given ID.
            DatabaseError: On unexpected database failure.
        """
        return self._repo.get_by_id(faq_id)

    def list_faqs(self, category: str | None = None) -> list[FaqResponseDTO]:
        """Return all FAQs ordered by category then display order.

        Args:
            category: Optionally filter by category name.

        Raises:
            DatabaseError: On unexpected database failure.
        """
        return self._repo.get_all(category=category)

    def list_categories(self) -> list[str]:
        """Return distinct FAQ category names for navigation/filtering.

        Raises:
            DatabaseError: On unexpected database failure.
        """
        return self._repo.get_categories()

    def update_faq(self, faq_id: str, updates: dict) -> FaqResponseDTO:
        """Update mutable fields of a FAQ.

        Raises:
            NotFound: If no FAQ exists with the given ID.
            AlreadyExists: If the update would cause a question conflict.
            DatabaseError: On unexpected database failure.
        """
        allowed = {"question", "answer", "category", "order"}
        safe_updates = {k: v for k, v in updates.items() if k in allowed}
        logger.info("Updating FAQ id=%s fields=%s", faq_id, list(safe_updates.keys()))
        result = self._repo.update(faq_id, safe_updates)
        logger.info("FAQ updated: id=%s", faq_id)
        return result

    def delete_faq(self, faq_id: str) -> None:
        """Permanently delete a FAQ.

        Raises:
            NotFound: If no FAQ exists with the given ID.
            DatabaseError: On unexpected database failure.
        """
        logger.info("Deleting FAQ id=%s", faq_id)
        self._repo.delete(faq_id)
        logger.info("FAQ deleted: id=%s", faq_id)
