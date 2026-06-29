from __future__ import annotations
import logging
from typing import Any, TYPE_CHECKING
from dataclasses import asdict

from tuned.dtos import ServiceCategoryDTO, ServiceCategoryResponseDTO, ServiceCategoryUpdateDTO
from tuned.dtos.audit import ActivityLogCreateDTO
from tuned.repository.exceptions import AlreadyExists, DatabaseError, NotFound
from tuned.core.logging import get_logger
from tuned.core.events import get_event_bus
from tuned.utils.variables import Variables
from tuned.interface.content.service_category_queries import ServiceCategoryQueryService

if TYPE_CHECKING:
    from tuned.repository import Repository

logger: logging.Logger = get_logger(__name__)
event_bus = get_event_bus()


class ServiceCategoryService(ServiceCategoryQueryService):
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
                action=action, user_id=user_id, entity_type=Variables.SERVICE_CATEGORY_ENTITY_TYPE,
                entity_id=entity_id, before=before, after=after, created_by=actor_id,
                ip_address="system", user_agent="system"
            ))
        except Exception as exc:
            logger.error("[%s] Audit failed for category %s: %r", self.__class__.__name__, entity_id, exc)

    def create_category(self, data: ServiceCategoryDTO, actor_id: str) -> ServiceCategoryResponseDTO:
        try:
            logger.info("Creating service category: %s", data.name)
            result = self._repo.create(data)
            logger.info("Service category created: id=%s", result.id)
            self._log_activity(Variables.SERVICE_CATEGORY_CREATE_ACTION, str(result.id), actor_id, after=asdict(result))
            self._repo.save()
            event_bus.emit("service_category.created", asdict(result))
            return result
        except AlreadyExists:
            self._repo.rollback()
            logger.error("Service category already exists: %s", data.name)
            raise AlreadyExists("Service category already exists")
        except DatabaseError:
            self._repo.rollback()
            logger.error("Database error while creating service category")
            raise DatabaseError("Database error while creating service category")

    def update_category(self, category_id: str, updates: ServiceCategoryUpdateDTO, actor_id: str) -> ServiceCategoryResponseDTO:
        try:
            logger.info("Updating service category id=%s", category_id)
            before_dto = asdict(self._repo.get_by_id(category_id))
            result = self._repo.update(category_id, updates)
            logger.info("Service category updated: id=%s", category_id)
            self._log_activity(Variables.SERVICE_CATEGORY_UPDATE_ACTION, category_id, actor_id, before=before_dto, after=asdict(result))
            self._repo.save()
            event_bus.emit("service_category.updated", asdict(result))
            return result
        except NotFound:
            self._repo.rollback()
            logger.error("Service category not found: %s", category_id)
            raise NotFound("Service category not found")
        except DatabaseError:
            self._repo.rollback()
            logger.error("Database error while updating service category")
            raise DatabaseError("Database error while updating service category")

    def delete_category(self, category_id: str, actor_id: str) -> None:
        try:
            logger.info("Deleting service category id=%s", category_id)
            before_dto = asdict(self._repo.get_by_id(category_id))
            self._repo.delete(category_id)
            logger.info("Service category deleted: id=%s", category_id)
            self._log_activity(Variables.SERVICE_CATEGORY_DELETE_ACTION, category_id, actor_id, before=before_dto)
            self._repo.save()
            event_bus.emit("service_category.deleted", {"id": category_id})
        except NotFound:
            self._repo.rollback()
            logger.error("Service category not found: %s", category_id)
            raise NotFound("Service category not found")
        except DatabaseError:
            self._repo.rollback()
            logger.error("Database error while deleting service category")
            raise DatabaseError("Database error while deleting service category")
