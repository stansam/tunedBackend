from __future__ import annotations
from typing import TYPE_CHECKING, Any
from dataclasses import asdict
from tuned.dtos import (
    TestimonialDTO, TestimonialResponseDTO, TestimonialUpdateDTO,
    TestimonialListRequestDTO, TestimonialListResponseDTO, AdminTestimonialListRequestDTO
)
from tuned.dtos.audit import ActivityLogCreateDTO
from tuned.repository.exceptions import AlreadyExists, DatabaseError, NotFound
from tuned.core.logging import get_logger
from tuned.core.events import get_event_bus
from tuned.utils.variables import Variables

if TYPE_CHECKING:
    from tuned.repository import Repository

logger = get_logger(__name__)
event_bus = get_event_bus()

class TestimonialService:
    def __init__(self, repos: Repository) -> None:
        self._repo = repos.testimonial
        from tuned.interface.audit import AuditService
        self._audit = AuditService(repos=repos)

    def _log_activity(self, action: str, entity_id: str, actor_id: str, before: Any = None, after: Any = None) -> None:
        try:
            self._audit.activity_log.log(ActivityLogCreateDTO(
                action=action, user_id=None if actor_id == "system" else actor_id,
                entity_type=Variables.TESTIMONIAL_ENTITY_TYPE, entity_id=entity_id,
                before=before, after=after, created_by=actor_id, ip_address="system", user_agent="system"
            ))
        except Exception as exc:
            logger.error("[TestimonialService] Audit failed: %r", exc)

    def create_testimonial(self, data: TestimonialDTO, actor_id: str = "system") -> TestimonialResponseDTO:
        try:
            res = self._repo.create(data)
            self._log_activity(Variables.TESTIMONIAL_CREATE_ACTION, res.id, actor_id, after=asdict(res))
            self._repo.save()
            event_bus.emit("testimonial.created", asdict(res))
            return res
        except AlreadyExists as e:
            self._repo.rollback()
            raise AlreadyExists(str(e))
        except DatabaseError as e:
            self._repo.rollback()
            raise DatabaseError(str(e))

    def get_testimonial(self, t_id: str) -> TestimonialResponseDTO:
        return self._repo.get_by_id(t_id)

    def list_approved_testimonials(self, svc_id: str | None = None) -> list[TestimonialResponseDTO]:
        return self._repo.get_approved(service_id=svc_id)

    def list_approved_paginated(self, req: TestimonialListRequestDTO) -> TestimonialListResponseDTO:
        return self._repo.get_approved_paginated(req)

    def list_pending_testimonials(self) -> list[TestimonialResponseDTO]:
        return self._repo.get_pending()

    def list_all_testimonials(self, req: AdminTestimonialListRequestDTO) -> TestimonialListResponseDTO:
        return self._repo.list_all(req)

    def approve_testimonial(self, t_id: str, actor_id: str = "system") -> TestimonialResponseDTO:
        try:
            before = asdict(self._repo.get_by_id(t_id))
            res = self._repo.approve(t_id)
            self._log_activity(Variables.TESTIMONIAL_APPROVE_ACTION, t_id, actor_id, before=before, after=asdict(res))
            self._repo.save()
            event_bus.emit("testimonial.updated", asdict(res))
            return res
        except (NotFound, DatabaseError):
            self._repo.rollback()
            raise

    def update_testimonial(self, t_id: str, updates: TestimonialUpdateDTO, actor_id: str = "system") -> TestimonialResponseDTO:
        try:
            before = asdict(self._repo.get_by_id(t_id))
            res = self._repo.update(t_id, updates)
            self._log_activity(Variables.TESTIMONIAL_UPDATE_ACTION, t_id, actor_id, before=before, after=asdict(res))
            self._repo.save()
            event_bus.emit("testimonial.updated", asdict(res))
            return res
        except (NotFound, DatabaseError):
            self._repo.rollback()
            raise

    def delete_testimonial(self, t_id: str, actor_id: str = "system") -> None:
        try:
            before = asdict(self._repo.get_by_id(t_id))
            self._repo.delete(t_id)
            self._log_activity(Variables.TESTIMONIAL_DELETE_ACTION, t_id, actor_id, before=before)
            self._repo.save()
            event_bus.emit("testimonial.deleted", {"id": t_id})
        except (NotFound, DatabaseError):
            self._repo.rollback()
            raise
