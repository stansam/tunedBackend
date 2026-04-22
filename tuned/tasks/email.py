from __future__ import annotations

from typing import Any

from celery.utils.log import get_task_logger

from tuned.celery_app import celery_app
from tuned.models import User
from tuned.extensions import db
from tuned.services.email_service import send_welcome_email

logger = get_task_logger(__name__)


@celery_app.task(
    name='tuned.tasks.email.send_transactional_email',
    bind=True,
    queue='email',
    max_retries=3,
    default_retry_delay=60,
    soft_time_limit=30,
    time_limit=60,
    acks_late=True,
)
def send_transactional_email(
    self,
    to: str,
    subject: str,
    template: str,
    context: dict[str, Any],
    sender: str | None = None,
) -> None:
    from tuned.utils.email import send_email
    try:
        send_email(to=to, subject=subject, template=template, sender=sender, **context)
        logger.info(f"[email] '{subject}' sent to {to}")

    except Exception as exc:
        attempt = self.request.retries
        delay = 60 * (2 ** attempt)  # 60s, 120s, 240s
        logger.warning(
            f"[email] Failed ({attempt}/{self.max_retries}) sending '{subject}' to {to}: "
            f"{exc!r} — retrying in {delay}s"
        )
        raise self.retry(exc=exc, countdown=delay)


@celery_app.task(
    name='tuned.tasks.email.send_welcome_task',
    bind=True,
    queue='email',
    max_retries=2,
    acks_late=True,
)
def send_welcome_task(self, user_id: str) -> None:
    from tuned.repository.user.get import GetUserByID
    from tuned.repository.exceptions import NotFound
    from tuned.extensions import db
    try:
        user: User = GetUserByID(db.session).execute(user_id)
        send_welcome_email(user)
    except NotFound:
        logger.warning(f"[email] send_welcome_task: user {user_id} not found — skipping")
    except Exception as exc:
        raise self.retry(exc=exc, countdown=120)