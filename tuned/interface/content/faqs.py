import logging

from tuned.dtos import FaqDTO, FaqResponseDTO
from tuned.repository import repositories
from tuned.repository.exceptions import AlreadyExists, DatabaseError, NotFound
from tuned.core.logging import get_logger

logger: logging.Logger = get_logger(__name__)


class FAQService:
    """Service layer for FAQ business logic."""

    def __init__(self) -> None:
        self._repo = repositories.faq

    def create_faq(self, data: FaqDTO) -> FaqResponseDTO:
        try:
            logger.info("Creating FAQ in category '%s'", data.category)
            result = self._repo.create(data)
            logger.info("FAQ created: id=%s", result.id)
            return result
        except AlreadyExists:
            logger.error("FAQ already exists: %s", data.question)
            raise AlreadyExists("FAQ already exists")
        except DatabaseError:
            logger.error("Database error while creating FAQ")
            raise DatabaseError("Database error while creating FAQ")

    def get_faq(self, faq_id: str) -> FaqResponseDTO:
        try:
            return self._repo.get_by_id(faq_id)
        except NotFound:
            logger.error("FAQ not found: %s", faq_id)
            raise NotFound("FAQ not found")
        except DatabaseError:
            logger.error("Database error while fetching FAQ")
            raise DatabaseError("Database error while fetching FAQ")

    def list_faqs(self, category: str | None = None) -> list[FaqResponseDTO]:
        try:
            return self._repo.get_all(category=category)
        except DatabaseError:
            logger.error("Database error while fetching FAQs")
            raise DatabaseError("Database error while fetching FAQs")

    def list_categories(self) -> list[str]:
        try:
            return self._repo.get_categories()
        except DatabaseError:
            logger.error("Database error while fetching FAQ categories")
            raise DatabaseError("Database error while fetching FAQ categories")

    def update_faq(self, faq_id: str, updates: dict) -> FaqResponseDTO:
        try:
            allowed = {"question", "answer", "category", "order"}
            safe_updates = {k: v for k, v in updates.items() if k in allowed}
            logger.info("Updating FAQ id=%s fields=%s", faq_id, list(safe_updates.keys()))
            result = self._repo.update(faq_id, safe_updates)
            logger.info("FAQ updated: id=%s", faq_id)
            return result
        except NotFound:
            logger.error("FAQ not found: %s", faq_id)
            raise NotFound("FAQ not found")
        except DatabaseError:
            logger.error("Database error while updating FAQ")
            raise DatabaseError("Database error while updating FAQ")

    def delete_faq(self, faq_id: str) -> None:
        try:
            logger.info("Deleting FAQ id=%s", faq_id)
            self._repo.delete(faq_id)
            logger.info("FAQ deleted: id=%s", faq_id)
        except NotFound:
            logger.error("FAQ not found: %s", faq_id)
            raise NotFound("FAQ not found")
        except DatabaseError:
            logger.error("Database error while deleting FAQ")
            raise DatabaseError("Database error while deleting FAQ")
