import re
from tuned.models import NotificationType
from tuned.celery_app import celery_app
from celery.utils.log import get_task_logger
from typing import Optional, Any
from celery import Task

logger = get_task_logger(__name__)

@celery_app.task(  # type: ignore[untyped-decorator]
    name='tuned.tasks.notifications.create_in_app_notification',
    bind=True,
    queue='notifications',
    max_retries=2,
    acks_late=True,
)
def create_in_app_notification(
    self: Task,
    user_id: str,
    title: str,
    message: str,
    notification_type: str = "info",
    action_url: Optional[str] = None,
    category: str = 'general',
) -> None:
    try:
        from tuned.utils.dependencies import get_services
        from tuned.dtos.notification import NotificationCreateDTO
        from tuned.extensions import socketio

        try:
            notif_type = NotificationType(notification_type.lower())
        except (ValueError, AttributeError):
            notif_type = NotificationType.INFO

        sanitized_url = None
        if action_url:
            trimmed_url = action_url.strip()
            if re.match(r'^(/|https?://)', trimmed_url, re.IGNORECASE) and not re.match(r'^(javascript|data):', trimmed_url, re.IGNORECASE):
                sanitized_url = trimmed_url

        dto = NotificationCreateDTO(
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notif_type,
            link=sanitized_url,
            category=category
        )
        notif = get_services().notification.create_notification(dto)

        socketio.emit(
            'notification:new',
            {
                'id': str(notif.id), 
                'title': title, 
                'message': message, 
                'type': notif_type.value,
                'link': action_url,
                'is_read': False,
                'created_at': notif.created_at.isoformat() if hasattr(notif.created_at, "isoformat") else notif.created_at
            },
            to=f'user_{user_id}',
        )
        logger.info("[notif] Created notification for user %s", user_id)

    except Exception as exc:
        logger.error("[notif] Error creating notification for user %s: %r", user_id, exc)
        raise self.retry(exc=exc, countdown=30)

@celery_app.task(
    name="tuned.tasks.notifications.push_unread_count_task",
    bind=True,
    queue="notifications",
    max_retries=1,
    acks_late=True,
)
def push_unread_count_task(self: Task, user_id: str) -> None:
    try:
        from tuned.utils.dependencies import get_services
        from tuned.extensions import socketio
        unread = get_services().notification.get_unread_count(user_id)
        socketio.emit("notification:count", {"unread_count": unread}, to=f"user_{user_id}")
    except Exception as exc:
        logger.error("[push_unread_count_task] Failed for user %s: %r", user_id, exc)
        raise self.retry(exc=exc, countdown=5)

