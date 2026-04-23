from __future__ import annotations

from datetime import datetime, timezone

from celery.utils.log import get_task_logger

from tuned.celery_app import celery_app

logger = get_task_logger(__name__)


@celery_app.task(
    name="tuned.tasks.dashboard_tasks.emit_actionable_alert",
    bind=True,
    queue="notifications",
    max_retries=2,
    acks_late=True,
)
def emit_actionable_alert(
    self,
    client_id:  str,
    alert_id:   str,
    alert_type: str,
    message:    str,
    metadata:   dict,
) -> None:
    logger.debug(
        "[emit_actionable_alert] Dispatching %s alert to user %s",
        alert_type, client_id,
    )
    try:
        from tuned.extensions import socketio
        socketio.emit(
            "actionable_alert.new",
            {
                "id":         alert_id,
                "type":       alert_type,
                "message":    message,
                "metadata":   metadata or {},
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
            room=f"user_{client_id}",
        )
        logger.info(
            "[emit_actionable_alert] Sent %s alert to user %s",
            alert_type, client_id,
        )
    except Exception as exc:
        logger.error("[emit_actionable_alert] Failed for user %s: %r", client_id, exc)
        raise self.retry(exc=exc, countdown=15)
