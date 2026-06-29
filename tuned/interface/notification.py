from __future__ import annotations
import logging
from typing import Optional, TYPE_CHECKING, Any
from tuned.dtos.notification import NotificationCreateDTO, NotificationResponseDTO

if TYPE_CHECKING:
    from tuned.repository import Repository
    from tuned.repository.user.notification import NotificationRepository

logger = logging.getLogger(__name__)

class NotificationInterface:
    def __init__(self, repos: Repository) -> None:
        self._repo = repos.notification

    def create_notification(self, data: NotificationCreateDTO) -> NotificationResponseDTO:
        notification = self._repo.create(data)
        self._repo.save()
        return notification

    def mark_read(self, notification_id: str, user_id: str) -> NotificationResponseDTO:
        notification = self._repo.mark_read(notification_id, user_id)
        self._repo.save()
        try:
            from tuned.core.events import get_event_bus
            get_event_bus().emit("notification.read", {
                "notification_id": str(notification_id),
                "user_id": str(user_id)
            })
        except Exception as e:
            logger.error("[NotificationInterface.mark_read] Event emit failed: %r", e)
        return notification

    def mark_all_read(self, user_id: str) -> int:
        updated_count = self._repo.mark_all_read(user_id)
        self._repo.save()
        try:
            from tuned.core.events import get_event_bus
            get_event_bus().emit("notification.all_read", {
                "user_id": str(user_id)
            })
        except Exception as e:
            logger.error("[NotificationInterface.mark_all_read] Event emit failed: %r", e)
        return updated_count

    def get_unread_count(self, user_id: str) -> int:
        return self._repo.get_unread_count(user_id)

    def delete_notification(self, notification_id: str, user_id: str) -> bool:
        res = self._repo.delete(notification_id, user_id)
        self._repo.save()
        return res

    def get_user_notifications(
        self,
        user_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> list[NotificationResponseDTO]:
        limit = max(1, min(limit, 100))
        offset = max(0, offset)
        return self._repo.get_user_notifications(user_id, limit, offset)

    def get_total_count(self, user_id: str) -> int:
        return self._repo.get_total_count(user_id)


class NotificationEventHandlers:
    def __init__(self, event_bus: Any) -> None:
        self._bus = event_bus

    def register(self) -> None:
        self._bus.on("notification.read", self._on_notification_read)
        self._bus.on("notification.all_read", self._on_notification_all_read)
        logger.info("[NotificationEventHandlers] registered")

    def _on_notification_read(self, payload: dict[str, Any]) -> None:
        try:
            from tuned.extensions import socketio
            user_id = payload.get("user_id")
            notification_id = payload.get("notification_id")
            if user_id and notification_id:
                socketio.emit(
                    "notification:read",
                    {"notification_id": str(notification_id)},
                    to=f"user_{user_id}",
                )
        except Exception as exc:
            logger.error("[NotificationEventHandlers._on_notification_read] Socket emit failed: %r", exc)

    def _on_notification_all_read(self, payload: dict[str, Any]) -> None:
        try:
            from tuned.extensions import socketio
            user_id = payload.get("user_id")
            if user_id:
                socketio.emit("notification:count", {"unread_count": 0}, to=f"user_{user_id}")
        except Exception as exc:
            logger.error("[NotificationEventHandlers._on_notification_all_read] Socket emit failed: %r", exc)


