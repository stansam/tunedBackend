from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import Callable
from tuned.repository.preferences.get import GetUserPreferences
from tuned.repository.preferences.update import UpdatePreferenceCategory
from tuned.repository.exceptions import DatabaseError
from tuned.models import (
    UserNotificationPreferences, UserEmailPreferences, UserPrivacySettings,
    UserLocalizationSettings, UserAccessibilityPreferences, UserBillingPreferences
)
from tuned.repository.preferences.update import PreferenceModel
from tuned.dtos import (
    AccessibilityDTO,
    AllPreferencesResponseDTO,
    BillingPreferenceDTO,
    EmailPreferenceDTO,
    LocalizationDTO,
    NotificationDTO,
    PreferenceResponseDTO,
    PreferenceUpdateDTO,
    PrivacyDTO,
)

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
        self._response_map: dict[str, Callable[[PreferenceModel], PreferenceResponseDTO]] = {
            "notification": NotificationDTO.from_model,
            "email": EmailPreferenceDTO.from_model,
            "privacy": PrivacyDTO.from_model,
            "localization": LocalizationDTO.from_model,
            "accessibility": AccessibilityDTO.from_model,
            "billing": BillingPreferenceDTO.from_model,
        }

    def get_all_preferences(self, user_id: str) -> AllPreferencesResponseDTO:
        return GetUserPreferences(self.session).execute(user_id)

    def update_category(
        self,
        category: str,
        user_id: str,
        data: PreferenceUpdateDTO,
    ) -> PreferenceResponseDTO:
        model = self._category_map.get(category)
        if not model:
            raise ValueError(f"Invalid preference category: {category}")
        response_factory = self._response_map[category]
        updated = UpdatePreferenceCategory(self.session).execute(
            model,
            user_id,
            data.to_update_dict(),
        )
        return response_factory(updated)

    def save(self) -> None:
        try:
            self.session.commit()
        except SQLAlchemyError as e:
            self.session.rollback()
            raise DatabaseError(f"Database error while saving preferences: {str(e)}") from e

    def rollback(self) -> None:
        self.session.rollback()
