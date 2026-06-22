from __future__ import annotations
import logging
from typing import Optional, TYPE_CHECKING, Any
from dataclasses import asdict

from tuned.dtos import (
    SampleDTO, SampleResponseDTO, SampleUpdateDTO, SampleListRequestDTO, 
    SampleListResponseDTO, SampleServiceResponseDTO
)
from tuned.dtos.audit import ActivityLogCreateDTO
from tuned.repository.exceptions import AlreadyExists, DatabaseError, NotFound
from tuned.core.logging import get_logger
from tuned.core.events import get_event_bus
from tuned.utils.variables import Variables

if TYPE_CHECKING:
    from tuned.repository import Repository

logger: logging.Logger = get_logger(__name__)
event_bus = get_event_bus()


class SampleService:
    def __init__(self, repos: Repository) -> None:
        self._repo = repos.sample
        from tuned.interface.audit import AuditService
        self._audit = AuditService(repos=repos)

    def _log_activity(self, action: str, entity_id: str, actor_id: str, before: Any = None, after: Any = None) -> None:
        try:
            user_id = None
            if actor_id != "system":
                user_id = actor_id

            self._audit.activity_log.log(ActivityLogCreateDTO(
                action=action, user_id=user_id, entity_type=Variables.SAMPLE_ENTITY_TYPE,
                entity_id=entity_id, before=before, after=after, created_by=actor_id,
                ip_address="system", user_agent="system"
            ))
        except Exception as exc:
            logger.error("[%s] Audit failed for sample %s: %r", self.__class__.__name__, entity_id, exc)

    def create_sample(self, data: SampleDTO, actor_id: str = "system") -> SampleResponseDTO:
        try:
            logger.info("Creating sample: %s", data.title)
            result = self._repo.create(data)
            logger.info("Sample created: id=%s", result.id)
            self._log_activity(Variables.SAMPLE_CREATE_ACTION, str(result.id), actor_id, after=asdict(result))
            self._repo.save()
            event_bus.emit("sample.created", asdict(result))
            return result
        except AlreadyExists:
            self._repo.rollback()
            logger.error("Sample already exists: %s", data.title)
            raise AlreadyExists("Sample already exists")
        except DatabaseError:
            self._repo.rollback()
            logger.error("Database error while creating sample")
            raise DatabaseError("Database error while creating sample")

    def get_sample(self, sample_id: str) -> SampleResponseDTO:
        try:
            return self._repo.get_by_id(sample_id)
        except NotFound:
            logger.error("Sample not found: %s", sample_id)
            raise NotFound("Sample not found")
        except DatabaseError:
            logger.error("Database error while fetching sample")
            raise DatabaseError("Database error while fetching sample")

    def get_sample_by_slug(self, slug: str) -> SampleResponseDTO:
        try:
            return self._repo.get_by_slug(slug)
        except NotFound:
            logger.error("Sample not found with slug: %s", slug)
            raise NotFound("Sample not found")
        except DatabaseError:
            logger.error("Database error while fetching sample by slug")
            raise DatabaseError("Database error while fetching sample by slug")

    def list_samples(self, req: SampleListRequestDTO) -> SampleListResponseDTO:
        try:
            return self._repo.list_all(req)
        except DatabaseError:
            logger.error("Database error while listing samples")
            raise DatabaseError("Database error while listing samples")

    def list_samples_by_service(self, service_id: str) -> list[SampleResponseDTO]:
        try:
            return self._repo.get_samples_by_service_id(service_id)
        except DatabaseError:
            logger.error("Database error while fetching samples by service")
            raise DatabaseError("Database error while fetching samples by service")

    def update_sample(self, sample_id: str, updates: SampleUpdateDTO, actor_id: str = "system") -> SampleResponseDTO:
        try:
            logger.info("Updating sample id=%s", sample_id)
            before_dto = asdict(self._repo.get_by_id(sample_id))
            result = self._repo.update(sample_id, updates)
            logger.info("Sample updated: id=%s", sample_id)
            self._log_activity(Variables.SAMPLE_UPDATE_ACTION, sample_id, actor_id, before=before_dto, after=asdict(result))
            self._repo.save()
            event_bus.emit("sample.updated", asdict(result))
            return result
        except NotFound:
            self._repo.rollback()
            logger.error("Sample not found: %s", sample_id)
            raise NotFound("Sample not found")
        except DatabaseError:
            self._repo.rollback()
            logger.error("Database error while updating sample")
            raise DatabaseError("Database error while updating sample")

    def delete_sample(self, sample_id: str, actor_id: str = "system") -> None:
        try:
            logger.info("Deleting sample id=%s", sample_id)
            before_dto = asdict(self._repo.get_by_id(sample_id))
            self._repo.delete(sample_id)
            logger.info("Sample deleted: id=%s", sample_id)
            self._log_activity(Variables.SAMPLE_DELETE_ACTION, sample_id, actor_id, before=before_dto)
            self._repo.save()
            event_bus.emit("sample.deleted", {"id": sample_id})
        except NotFound:
            self._repo.rollback()
            logger.error("Sample not found: %s", sample_id)
            raise NotFound("Sample not found")
        except DatabaseError:
            self._repo.rollback()
            logger.error("Database error while deleting sample")
            raise DatabaseError("Database error while deleting sample")


    def list_featured_samples(self) -> list[SampleResponseDTO]:
        try:
            return self._repo.get_featured()
        except DatabaseError:
            logger.error("Database error while fetching featured samples")
            raise DatabaseError("Database error while fetching featured samples")

    def get_sample_services(self) -> list[SampleServiceResponseDTO]:
        try:
            return list(self._repo.get_distinct_services())
        except DatabaseError:
            logger.error("Database error while fetching sample services")
            raise DatabaseError("Database error while fetching sample services")

    def get_related_samples(self, slug: str) -> list[SampleResponseDTO]:
        try:
            return list(self._repo.get_related_samples(slug))
        except DatabaseError:
            logger.error("Database error while fetching related samples: %s", slug)
            raise DatabaseError("Database error while fetching related samples")