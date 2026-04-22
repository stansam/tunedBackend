import logging
from dataclasses import asdict
from tuned.repository.user.notification import NotificationRepository
from tuned.dtos.notification import NotificationCreateDTO, NotificationResponseDTO
from tuned.extensions import db

logger = logging.getLogger(__name__)

class NotificationInterface:
    def __init__(self):
        self._repo = NotificationRepository(db.session)

    def create_notification(self, data: NotificationCreateDTO) -> NotificationResponseDTO:
        return self._repo.create(data)

    def mark_read(self, notification_id: str) -> bool:
        return self._repo.mark_read(notification_id)

    def mark_all_read(self, user_id: str) -> int:
        return self._repo.mark_all_read(user_id)

    def get_unread_count(self, user_id: str) -> int:
        return self._repo.get_unread_count(user_id)

    def get_user_notifications(self, user_id: str, limit: int = 20, offset: int = 0) -> list[dict]:
        notifications = self._repo.get_user_notifications(user_id, limit, offset)
        return [asdict(NotificationResponseDTO.from_model(n)) for n in notifications]
