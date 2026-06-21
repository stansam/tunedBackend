from __future__ import annotations
import logging
from typing import Any, TYPE_CHECKING
from dataclasses import asdict

from tuned.dtos import ServiceDTO, ServiceResponseDTO, ServiceUpdateDTO
from tuned.dtos.audit import ActivityLogCreateDTO
from tuned.repository.exceptions import AlreadyExists, DatabaseError, NotFound
from tuned.core.logging import get_logger
from tuned.core.events import get_event_bus
from tuned.utils.variables import Variables
from tuned.interface.content.services_queries import ServiceQueryService

if TYPE_CHECKING:
    from tuned.repository import Repository

logger: logging.Logger = get_logger(__name__)
event_bus = get_event_bus()


class ServiceService(ServiceQueryService):
    def __init__(self, repos: Repository) -> None:
        super().__init__(repos)
        from tuned.interface.audit import AuditService
        self._audit = AuditService(repos=repos)

    def _log_activity(self, action: str, entity_id: str, actor_id: str, before: Any = None, after: Any = None) -> None:
        try:
            user_id = None
            if actor_id != "system":
                user_id = actor_id

            self._audit.activity_log.log(ActivityLogCreateDTO(
                action=action, user_id=user_id, entity_type=Variables.SERVICE_ENTITY_TYPE,
                entity_id=entity_id, before=before, after=after, created_by=actor_id,
                ip_address="system", user_agent="system"
            ))
        except Exception as exc:
            logger.error("[%s] Audit failed for service %s: %r", self.__class__.__name__, entity_id, exc)

    def create_service(self, data: ServiceDTO, actor_id: str) -> ServiceResponseDTO:
        try:
            logger.info("Creating service: %s", data.name)
            result = self._repo.create(data)
            logger.info("Service created: id=%s", result.id)
            self._log_activity(Variables.SERVICE_CREATE_ACTION, str(result.id), actor_id, after=asdict(result))
            self._repo.save()
            event_bus.emit("service.created", asdict(result))
            return result
        except AlreadyExists:
            self._repo.rollback()
            logger.error("Service already exists: %s", data.name)
            raise AlreadyExists("Service already exists")
        except DatabaseError:
            self._repo.rollback()
            logger.error("Database error while creating service")
            raise DatabaseError("Database error while creating service")

    def update_service(self, service_id: str, updates: ServiceUpdateDTO, actor_id: str) -> ServiceResponseDTO:
        try:
            logger.info("Updating service id=%s", service_id)
            before_dto = asdict(self._repo.get_by_id(service_id))
            result = self._repo.update(service_id, updates)
            logger.info("Service updated: id=%s", service_id)
            self._log_activity(Variables.SERVICE_UPDATE_ACTION, service_id, actor_id, before=before_dto, after=asdict(result))
            self._repo.save()
            event_bus.emit("service.updated", asdict(result))
            return result
        except NotFound:
            self._repo.rollback()
            logger.error("Service not found: %s", service_id)
            raise NotFound("Service not found")
        except DatabaseError:
            self._repo.rollback()
            logger.error("Database error while updating service")
            raise DatabaseError("Database error while updating service")

    def delete_service(self, service_id: str, actor_id: str) -> None:
        try:
            logger.info("Deleting service id=%s", service_id)
            before_dto = asdict(self._repo.get_by_id(service_id))
            self._repo.delete(service_id)
            logger.info("Service deleted: id=%s", service_id)
            self._log_activity(Variables.SERVICE_DELETE_ACTION, service_id, actor_id, before=before_dto)
            self._repo.save()
            event_bus.emit("service.deleted", {"id": service_id})
        except NotFound:
            self._repo.rollback()
            logger.error("Service not found: %s", service_id)
            raise NotFound("Service not found")
        except DatabaseError:
            self._repo.rollback()
            logger.error("Database error while deleting service")
            raise DatabaseError("Database error while deleting service")