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
    notification_type: NotificationType = NotificationType.INFO,
    action_url: Optional[str] = None,
    category: str = 'general',
) -> None:
    try:
        from tuned.utils.dependencies import get_services
        from tuned.dtos.notification import NotificationCreateDTO
        from tuned.extensions import socketio

        dto = NotificationCreateDTO(
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type,
            link=action_url,
            category=category
        )
        notif = get_services().notification.create_notification(dto)

        socketio.emit(
            'notification:new',
            {
                'id': notif.id, 
                'title': title, 
                'message': message, 
                'type': notification_type,
                'link': action_url,
                'is_read': False,
                'created_at': notif.created_at
            },
            room=f'user_{user_id}',
        )
        logger.info(f"[notif] Created notification for user {user_id}")

    except Exception as exc:
        logger.error(f"[notif] Error creating notification for user {user_id}: {exc!r}")
        raise self.retry(exc=exc, countdown=30)

@celery_app.task  # type: ignore[untyped-decorator]
def test_flask_context() -> Any:
    from flask import current_app
    return current_app.config.get("APP_VERSION")