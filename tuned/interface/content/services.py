from __future__ import annotations
import logging
from typing import Optional, TYPE_CHECKING, List, Tuple

from tuned.dtos import ServiceDTO, ServiceResponseDTO, ServiceUpdateDTO
from tuned.repository.exceptions import AlreadyExists, DatabaseError, NotFound
from tuned.core.logging import get_logger

if TYPE_CHECKING:
    from tuned.repository import Repository

logger: logging.Logger = get_logger(__name__)


class ServiceService:
    def __init__(self, repos: Optional[Repository] = None) -> None:
        if repos:
            self._repo = repos.service
        else:
            from tuned.repository import repositories
            self._repo = repositories.service

    def create_service(self, data: ServiceDTO) -> ServiceResponseDTO:
        try:
            logger.info("Creating service: %s", data.name)
            result = self._repo.create(data)
            logger.info("Service created: id=%s", result.id)
            return result
        except AlreadyExists:
            logger.error("Service already exists: %s", data.name)
            raise AlreadyExists("Service already exists")
        except DatabaseError:
            logger.error("Database error while creating service")
            raise DatabaseError("Database error while creating service")

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

    def update_service(self, service_id: str, updates: ServiceUpdateDTO) -> ServiceResponseDTO:
        try:
            logger.info("Updating service id=%s", service_id)
            result = self._repo.update(service_id, updates)
            logger.info("Service updated: id=%s", service_id)
            return result
        except NotFound:
            logger.error("Service not found: %s", service_id)
            raise NotFound("Service not found")
        except DatabaseError:
            logger.error("Database error while updating service")
            raise DatabaseError("Database error while updating service")

    def delete_service(self, service_id: str) -> None:
        try:
            logger.info("Deleting service id=%s", service_id)
            self._repo.delete(service_id)
            logger.info("Service deleted: id=%s", service_id)
        except NotFound:
            logger.error("Service not found: %s", service_id)
            raise NotFound("Service not found")
        except DatabaseError:
            logger.error("Database error while deleting service")
            raise DatabaseError("Database error while deleting service")

    def get_service_mix(self, client_id: str) -> List[Tuple[str, int]]:
        try:
            return self._repo.get_service_mix(client_id)
        except DatabaseError:
            logger.error("Database error while fetching service mix for client %s", client_id)
            raise DatabaseError("Database error while fetching service mix")