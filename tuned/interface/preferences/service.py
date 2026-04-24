import logging
from typing import Any, Dict
from tuned.dtos.preferences import (
    LocalizationDTO, NotificationDTO, EmailPreferenceDTO,
    PrivacyDTO, AccessibilityDTO, BillingPreferenceDTO, AllPreferencesResponseDTO
)
from tuned.repository import repositories
from tuned.core.logging import get_logger
from tuned.interface.audit.activity_log import ActivityLogService
from tuned.dtos.audit import ActivityLogCreateDTO
from tuned.core.events import get_event_bus

logger: logging.Logger = get_logger(__name__)

class PreferenceService:
    def __init__(self) -> None:
        self._repo = repositories.preferences
        self._audit_service = ActivityLogService()
        self._event_bus = get_event_bus()

    def get_user_preferences(self, user_id: str) -> AllPreferencesResponseDTO:
        try:
            prefs = self._repo.get_all_preferences(user_id)
            return AllPreferencesResponseDTO(
                localization=LocalizationDTO.from_model(prefs["localization"]),
                notification=NotificationDTO.from_model(prefs["notification"]),
                email=EmailPreferenceDTO.from_model(prefs["email"]),
                privacy=PrivacyDTO.from_model(prefs["privacy"]),
                accessibility=AccessibilityDTO.from_model(prefs["accessibility"]),
                billing=BillingPreferenceDTO.from_model(prefs["billing"])
            )
        except Exception as e:
            logger.error(f"Error fetching preferences for user {user_id}: {str(e)}")
            raise

    def update_category(self, category: str, user_id: str, data: dict, locale: Any = None) -> bool:
        try:
            all_prefs = self._repo.get_all_preferences(user_id)
            old_obj = all_prefs.get(category)
            before_snapshot = self._get_snapshot(old_obj) if old_obj else {}

            updated_obj = self._repo.update_category(category, user_id, data)
            after_snapshot = self._get_snapshot(updated_obj)
            
            audit_data = ActivityLogCreateDTO(
                action=f"update_{category}_preferences",
                user_id=user_id,
                entity_type="user_preferences",
                entity_id=user_id,
                before=before_snapshot,
                after=after_snapshot,
                ip_address=getattr(locale, 'ip_address', None) if locale else None,
                user_agent=getattr(locale, 'user_agent', None) if locale else None
            )
            self._audit_service.log(audit_data)

            self._event_bus.emit("SETTINGS_UPDATED", {
                "user_id": user_id,
                "category": category,
                "payload": data
            })

            return True
        except Exception as e:
            logger.error(f"Error updating {category} preferences for user {user_id}: {str(e)}")
            return False

    def _get_snapshot(self, obj) -> Dict[str, Any]:
        if not obj: return {}
        return {c.name: str(getattr(obj, c.name)) if hasattr(getattr(obj, c.name), 'value') else getattr(obj, c.name) 
                for c in obj.__table__.columns if c.name not in ['user_id', 'id', 'created_at', 'updated_at']}
