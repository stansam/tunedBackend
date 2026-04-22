from tuned.core.events import get_event_bus
from tuned.models.enums import NotificationType
import logging

logger = logging.getLogger(__name__)

event_bus = get_event_bus()

def _on_user_registered(payload: dict) -> None:
    from tuned.services.email_service import send_verification_email
    from tuned.tasks.email import send_welcome_task
    from tuned.repository.user.get import GetUserByID
    from tuned.extensions import db

    user_id = payload.get('user_id')
    raw_token = payload.get('raw_token')

    try:
        user = GetUserByID(db.session).execute(str(user_id))
        send_verification_email(user, raw_token)
        send_welcome_task.apply_async(args=[user_id], countdown=1800, queue='email')
    except Exception as e:
        logger.error(f"[_on_user_registered] Error: {e}")

def _on_resend_verification_email(payload: dict) -> None:
    from tuned.services.email_service import send_verification_email
    from tuned.repository.user.get import GetUserByID
    from tuned.extensions import db

    user_id = payload.get('user_id')
    raw_token = payload.get('raw_token')

    try:
        user = GetUserByID(db.session).execute(str(user_id))
        send_verification_email(user, raw_token)
    except Exception as e:
        logger.error(f"[_on_resend_verification_email] Error: {e}")

def _on_email_verified(payload: dict) -> None:
    from tuned.tasks.notifications import create_in_app_notification
    user_id = payload.get('user_id')
    create_in_app_notification.delay(
        user_id=user_id,
        title='Email Verified',
        message='Your email has been verified. Welcome to TunedEssays!',
        notification_type=NotificationType.SUCCESS.value.upper(),
    )

def _on_password_changed(payload: dict) -> None:
    from tuned.tasks.notifications import create_in_app_notification
    user_id = payload.get('user_id')
    create_in_app_notification.delay(
        user_id=user_id,
        title='Password Changed',
        message="Your password has been successfully updated. If this wasn't you, please contact support immediately.",
        notification_type=NotificationType.WARNING.value.upper(),
    )

def register_all_handlers() -> None:
    event_bus.on('user.registered', _on_user_registered)
    event_bus.on('user.resend_verification_email', _on_resend_verification_email)
    event_bus.on('user.email_verified', _on_email_verified)
    event_bus.on('user.password_changed', _on_password_changed)
    logger.info("[EventBus] All event handlers registered")
