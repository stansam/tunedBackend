from typing import TYPE_CHECKING
from tuned.dtos import ServiceCategoryResponseDTO
from tuned.repository.exceptions import DatabaseError, NotFound
import logging
from tuned.core.logging import get_logger

if TYPE_CHECKING:
    from tuned.repository import Repository

logger: logging.Logger = get_logger(__name__)


class ServiceCategoryQueryService:
    def __init__(self, repos: Repository) -> None:
        self._repo = repos.service_category
        self._repos = repos

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
