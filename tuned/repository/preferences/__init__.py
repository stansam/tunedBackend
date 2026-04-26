from sqlalchemy.orm import Session
from typing import Any
from tuned.repository.preferences.get import GetUserPreferences
from tuned.repository.preferences.update import UpdatePreferenceCategory
from tuned.models import (
    UserNotificationPreferences, UserEmailPreferences, UserPrivacySettings,
    UserLocalizationSettings, UserAccessibilityPreferences, UserBillingPreferences
)
from tuned.dtos import AllPreferencesResponseDTO

class PreferenceRepository:
    def __init__(self, session: Session) -> None:
        self.session = session
        self._category_map = {
            "notification": UserNotificationPreferences,
            "email": UserEmailPreferences,
            "privacy": UserPrivacySettings,
            "localization": UserLocalizationSettings,
            "accessibility": UserAccessibilityPreferences,
            "billing": UserBillingPreferences
        }

    def get_all_preferences(self, user_id: str) -> AllPreferencesResponseDTO:
        return GetUserPreferences(self.session).execute(user_id)

    def update_category(self, category: str, user_id: str, data: dict[str, Any]) -> Any:
        model = self._category_map.get(category)
        if not model:
            raise ValueError(f"Invalid preference category: {category}")
        return UpdatePreferenceCategory(self.session).execute(model, user_id, data)
