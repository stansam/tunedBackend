from __future__ import annotations
import logging
from typing import Optional, TYPE_CHECKING
from tuned.dtos.notification import NotificationCreateDTO, NotificationResponseDTO

if TYPE_CHECKING:
    from tuned.repository import Repository
    from tuned.repository.user.notification import NotificationRepository

logger = logging.getLogger(__name__)

class NotificationInterface:
    def __init__(self, repos: Optional[Repository] = None, repo: Optional[NotificationRepository] = None) -> None:
        if repos:
            self._repo = repo or repos.notification
        else:
            from tuned.repository import repositories
            self._repo = repo or repositories.notification

    def create_notification(self, data: NotificationCreateDTO) -> NotificationResponseDTO:
        notification = self._repo.create(data)
        self._repo.save()
        return notification

    def mark_read(self, notification_id: str, user_id: str) -> NotificationResponseDTO:
        notification = self._repo.mark_read(notification_id, user_id)
        self._repo.save()
        return notification

    def mark_all_read(self, user_id: str) -> int:
        updated_count = self._repo.mark_all_read(user_id)
        self._repo.save()
        return updated_count

    def get_unread_count(self, user_id: str) -> int:
        return self._repo.get_unread_count(user_id)

    def get_user_notifications(
        self,
        user_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> list[NotificationResponseDTO]:
        return self._repo.get_user_notifications(user_id, limit, offset)
