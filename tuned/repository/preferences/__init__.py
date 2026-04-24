from tuned.repository.preferences.get import GetUserPreferences
from tuned.repository.preferences.update import UpdatePreferenceCategory
from tuned.extensions import db
from tuned.models import (
    UserNotificationPreferences, UserEmailPreferences, UserPrivacySettings,
    UserLocalizationSettings, UserAccessibilityPreferences, UserBillingPreferences
)

class PreferenceRepository:
    def __init__(self):
        self.db = db
        self._category_map = {
            "notification": UserNotificationPreferences,
            "email": UserEmailPreferences,
            "privacy": UserPrivacySettings,
            "localization": UserLocalizationSettings,
            "accessibility": UserAccessibilityPreferences,
            "billing": UserBillingPreferences
        }

    def get_all_preferences(self, user_id: str):
        return GetUserPreferences(self.db.session).execute(user_id)

    def update_category(self, category: str, user_id: str, data: dict):
        model = self._category_map.get(category)
        if not model:
            raise ValueError(f"Invalid preference category: {category}")
        return UpdatePreferenceCategory(self.db.session).execute(model, user_id, data)
