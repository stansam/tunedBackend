from __future__ import annotations
import logging
from typing import Optional, TYPE_CHECKING

from tuned.dtos import ServiceDTO, ServiceResponseDTO, ServiceListRequestDTO
from tuned.repository.exceptions import AlreadyExists, DatabaseError, NotFound
from tuned.core.logging import get_logger

if TYPE_CHECKING:
    from tuned.repository import Repository

logger: logging.Logger = get_logger(__name__)


class ServiceService:
    """Service layer for main service business logic."""

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

    def list_services(self, req: Optional[ServiceListRequestDTO] = None) -> list[ServiceResponseDTO]:
        try:
            if req:
                return self._repo.get_filtered(req)
            return self._repo.get_all()
        except DatabaseError:
            logger.error("Database error while fetching services")
            raise DatabaseError("Database error while fetching services")

    def update_service(self, service_id: str, updates: dict) -> ServiceResponseDTO:
        try:
            allowed = {"name", "description", "category_id", "base_price", "is_active", "display_order"}
            safe_updates = {k: v for k, v in updates.items() if k in allowed}
            logger.info("Updating service id=%s fields=%s", service_id, list(safe_updates.keys()))
            result = self._repo.update(service_id, safe_updates)
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