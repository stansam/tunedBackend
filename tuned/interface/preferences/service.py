from __future__ import annotations
import logging
from dataclasses import asdict, is_dataclass
from enum import Enum
from typing import Any, Optional, cast, TYPE_CHECKING
from tuned.dtos.preferences import AllPreferencesResponseDTO, PreferenceResponseDTO, PreferenceUpdateDTO
from tuned.core.logging import get_logger
from tuned.dtos.audit import ActivityLogCreateDTO
from tuned.core.events import EventBus, get_event_bus
from tuned.dtos.base import BaseRequestDTO
from tuned.repository.protocols import PreferenceRepositoryProtocol

if TYPE_CHECKING:
    from tuned.repository import Repository
    from tuned.interface.protocols import ActivityLogServiceProtocol
    from tuned.interface.audit import AuditService

logger: logging.Logger = get_logger(__name__)

class PreferenceService:
    def __init__(
        self,
        repos: Optional[Repository] = None,
        repo: Optional[PreferenceRepositoryProtocol] = None,
        audit_service: Optional[ActivityLogServiceProtocol] = None,
        event_bus: Optional[EventBus] = None,
    ) -> None:
        self._repo: PreferenceRepositoryProtocol
        self._audit: Optional[AuditService] = None
        self._audit_service: ActivityLogServiceProtocol

        if repos:
            self._repo = repo or repos.preferences
            from tuned.interface.audit import AuditService as AuditAggregator
            self._audit = AuditAggregator(repos=repos)
            self._audit_service = audit_service or self._audit.activity_log
        else:
            from tuned.repository import repositories
            self._repo = repo or repositories.preferences
            from tuned.interface.audit import audit_service as global_audit_agg
            self._audit = global_audit_agg
            self._audit_service = audit_service or self._audit.activity_log
            
        self._event_bus = event_bus or get_event_bus()

    def get_user_preferences(self, user_id: str) -> AllPreferencesResponseDTO:
        try:
            return self._repo.get_all_preferences(user_id)
        except Exception as e:
            logger.error(f"Error fetching preferences for user {user_id}: {str(e)}")
            raise

    def update_category(
        self,
        category: str,
        user_id: str,
        data: PreferenceUpdateDTO,
        locale: BaseRequestDTO | None = None,
    ) -> PreferenceResponseDTO:
        try:
            all_prefs = self._repo.get_all_preferences(user_id)
            before_snapshot = self._get_snapshot(getattr(all_prefs, category, None))

            updated_obj = self._repo.update_category(category, user_id, data)
            self._repo.save()
            after_snapshot = self._get_snapshot(updated_obj)
            
            audit_data = ActivityLogCreateDTO(
                action=f"update_{category}_preferences",
                user_id=user_id,
                entity_type="user_preferences",
                entity_id=user_id,
                before=before_snapshot,
                after=after_snapshot,
                ip_address=locale.ip_address if locale else "unknown",
                user_agent=locale.user_agent if locale else "unknown",
                created_by=user_id
            )
            self._audit_service.log(audit_data)

            self._event_bus.emit("SETTINGS_UPDATED", {
                "user_id": user_id,
                "category": category,
                "payload": after_snapshot
            })

            return updated_obj
        except Exception as e:
            self._repo.rollback()
            logger.error(f"Error updating {category} preferences for user {user_id}: {str(e)}")
            raise

    def _get_snapshot(self, obj: object) -> dict[str, Any]:
        if obj is None:
            return {}
        if is_dataclass(obj):
            snapshot = self._normalize_snapshot(asdict(cast(Any, obj)))
            return cast(dict[str, Any], snapshot)
        return {}

    def _normalize_snapshot(self, value: object) -> Any:
        if isinstance(value, Enum):
            return value.value
        if isinstance(value, dict):
            return {
                str(key): self._normalize_snapshot(item)
                for key, item in value.items()
            }
        if isinstance(value, list):
            return [self._normalize_snapshot(item) for item in value]
        return value
