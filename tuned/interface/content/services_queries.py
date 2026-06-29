from typing import TYPE_CHECKING, List, Tuple
from tuned.dtos import ServiceResponseDTO
from tuned.repository.exceptions import DatabaseError, NotFound
import logging
from tuned.core.logging import get_logger

if TYPE_CHECKING:
    from tuned.repository import Repository

logger: logging.Logger = get_logger(__name__)


class ServiceQueryService:
    def __init__(self, repos: Repository) -> None:
        self._repo = repos.service
        self._repos = repos

    def get_service(self, service_id: str) -> ServiceResponseDTO:
        try:
            return self._repo.get_by_id(service_id)
        except NotFound:
            logger.error("Service not found: %s", service_id)
            raise NotFound("Service not found")
        except DatabaseError:
            logger.error("Database error while fetching service")
            raise DatabaseError("Database error while fetching service")

    def get_service_by_slug(self, slug: str) -> ServiceResponseDTO:
        try:
            return self._repo.get_by_slug(slug)
        except NotFound:
            logger.error("Service not found with slug: %s", slug)
            raise NotFound("Service not found")
        except DatabaseError:
            logger.error("Database error while fetching service by slug")
            raise DatabaseError("Database error while fetching service by slug")

    def list_services(self, active_only: bool = True) -> list[ServiceResponseDTO]:
        try:
            return self._repo.get_all(active_only=active_only)
        except DatabaseError:
            logger.error("Database error while fetching services")
            raise DatabaseError("Database error while fetching services")

    def list_featured_services(self) -> list[ServiceResponseDTO]:
        try:
            return self._repo.get_featured()
        except DatabaseError:
            logger.error("Database error while fetching featured services")
            raise DatabaseError("Database error while fetching featured services")

    def list_services_by_category(self, category_id: str) -> list[ServiceResponseDTO]:
        try:
            return self._repo.get_services_by_category(category_id)
        except DatabaseError:
            logger.error("Database error while fetching services by category")
            raise DatabaseError("Database error while fetching services by category")

    def get_service_mix(self, client_id: str) -> List[Tuple[str, int]]:
        try:
            return self._repo.get_service_mix(client_id)
        except DatabaseError:
            logger.error("Database error while fetching service mix for client %s", client_id)
            raise DatabaseError("Database error while fetching service mix")
