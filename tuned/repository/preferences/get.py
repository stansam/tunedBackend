from tuned.models import (
    UserNotificationPreferences, UserEmailPreferences, UserPrivacySettings,
    UserLocalizationSettings, UserAccessibilityPreferences, UserBillingPreferences
)
from sqlalchemy.orm import Session
from tuned.repository.exceptions import DatabaseError
from sqlalchemy.exc import SQLAlchemyError

class GetUserPreferences:
    def __init__(self, db: Session):
        self.db = db

    def execute(self, user_id: str):
        try:
            return {
                "notification": self._get_or_create(UserNotificationPreferences, user_id),
                "email": self._get_or_create(UserEmailPreferences, user_id),
                "privacy": self._get_or_create(UserPrivacySettings, user_id),
                "localization": self._get_or_create(UserLocalizationSettings, user_id),
                "accessibility": self._get_or_create(UserAccessibilityPreferences, user_id),
                "billing": self._get_or_create(UserBillingPreferences, user_id)
            }
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching preferences: {str(e)}")

    def _get_or_create(self, model, user_id: str):
        obj = self.db.query(model).filter_by(user_id=user_id).first()
        if not obj:
            obj = model(user_id=user_id)
            self.db.add(obj)
            self.db.flush()
        return obj
