from tuned.models import (
    UserNotificationPreferences, UserEmailPreferences, UserPrivacySettings,
    UserLocalizationSettings, UserAccessibilityPreferences, UserBillingPreferences
)
from tuned.repository.exceptions import DatabaseError
from tuned.dtos import AllPreferencesResponseDTO, LocalizationDTO, NotificationDTO, EmailPreferenceDTO, PrivacyDTO, AccessibilityDTO, BillingPreferenceDTO
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from typing import Any
from typing import TypeVar, Type

T = TypeVar("T")

class GetUserPreferences:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, user_id: str) -> AllPreferencesResponseDTO:
        try:
            notification = self._get_or_create(UserNotificationPreferences, user_id)
            email = self._get_or_create(UserEmailPreferences, user_id)
            privacy = self._get_or_create(UserPrivacySettings, user_id)
            localization = self._get_or_create(UserLocalizationSettings, user_id)
            accessibility = self._get_or_create(UserAccessibilityPreferences, user_id)
            billing = self._get_or_create(UserBillingPreferences, user_id)
            
            response = AllPreferencesResponseDTO(
                notification=NotificationDTO.from_model(notification),
                email=EmailPreferenceDTO.from_model(email),
                privacy=PrivacyDTO.from_model(privacy),
                localization=LocalizationDTO.from_model(localization),
                accessibility=AccessibilityDTO.from_model(accessibility),
                billing=BillingPreferenceDTO.from_model(billing)
            )
            return response
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching preferences: {str(e)}")

    def _get_or_create(self, model: type[T], user_id: str) -> T:
        obj = self.session.query(model).filter_by(user_id=user_id).first()
        if not obj:
            obj = model(user_id=user_id)
            self.session.add(obj)
            self.session.flush()
            self.session.commit()
        return obj
