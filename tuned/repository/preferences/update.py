from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from tuned.repository.exceptions import DatabaseError
from tuned.models.preferences import (
    UserAccessibilityPreferences,
    UserBillingPreferences,
    UserEmailPreferences,
    UserLocalizationSettings,
    UserNotificationPreferences,
    UserPrivacySettings,
)

PreferenceModel = (
    UserNotificationPreferences
    | UserEmailPreferences
    | UserPrivacySettings
    | UserLocalizationSettings
    | UserAccessibilityPreferences
    | UserBillingPreferences
)
PreferenceModelType = (
    type[UserNotificationPreferences]
    | type[UserEmailPreferences]
    | type[UserPrivacySettings]
    | type[UserLocalizationSettings]
    | type[UserAccessibilityPreferences]
    | type[UserBillingPreferences]
)

class UpdatePreferenceCategory:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(
        self,
        model: PreferenceModelType,
        user_id: str,
        data: dict[str, object],
    ) -> PreferenceModel:
        try:
            stmt = select(model).where(getattr(model, "user_id") == user_id)
            obj = self.session.scalar(stmt)
            if not obj:
                obj = model(user_id=user_id)
                self.session.add(obj)

            for key, value in data.items():
                if hasattr(obj, key):
                    setattr(obj, key, value)
            
            self.session.flush()
            return obj
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while updating preference category: {str(e)}") from e
