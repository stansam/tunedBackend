from __future__ import annotations

from tuned.core.events import EventBus, EventPayload
from tuned.core.logging import get_logger
import logging
from typing import cast, Any, Optional
from datetime import datetime, timezone

logger: logging.Logger = get_logger(__name__)


class UserEventHandlers:
    def __init__(self, event_bus: EventBus) -> None:
        self._bus = event_bus

    def register(self) -> None:
        self._bus.on("user.registered",                self._on_registered)
        self._bus.on("user.resend_verification_email", self._on_resend_verification)
        self._bus.on("user.email_verified",            self._on_email_verified)
        self._bus.on("user.password_changed",          self._on_password_changed)
        logger.info("[UserEventHandlers] registered")

    def _on_registered(self, payload: EventPayload) -> None:
        from tuned.services.email_service import send_verification_email
        from tuned.utils.dependencies import get_services

        user_id    = payload.get("user_id")
        raw_token  = payload.get("raw_token")
        ip_address = payload.get("ip_address")

        if user_id is None:
            logger.error("[UserEventHandlers._on_registered] user_id missing in payload")
            return

        try:
            services = get_services()
            services.user.init_user_preferences(str(user_id))
        except Exception as exc:
            logger.error("[UserEventHandlers._on_registered] init_preferences failed: %r", exc)

        # Geolocation logic - dispatch Celery task
        if ip_address and ip_address not in ("127.0.0.1", "localhost", "unknown"):
            try:
                from tuned.tasks.user_tasks import update_user_geolocation
                update_user_geolocation.apply_async(
                    args=[str(user_id), ip_address],
                    countdown=0,
                    queue="notifications",
                )
            except Exception as celery_exc:
                logger.warning("[UserEventHandlers._on_registered] Geolocation task failed: %r", celery_exc)

        # Socket notification to admin room
        try:
            from tuned.extensions import socketio
            socketio.emit(
                "admin:user:registered",
                {"user_id": str(user_id), "created_at": datetime.now(timezone.utc).isoformat()},
                to="admin_room",
            )
        except Exception as socket_exc:
            logger.error("[UserEventHandlers._on_registered] Admin socket failed: %r", socket_exc)

        # Verification email
        try:
            user = get_services().user.get_user_obj(str(user_id))
            send_verification_email(user, str(raw_token or ""))
        except Exception as exc:
            logger.error("[UserEventHandlers._on_registered] Verification email failed: %r", exc)

        # Welcome email (delayed)
        try:
            from tuned.tasks.email import send_welcome_task
            send_welcome_task.apply_async(
                args=[str(user_id)], countdown=1800, queue="email"
            )
        except Exception as celery_exc:
            logger.warning("[UserEventHandlers._on_registered] Welcome task dispatch failed: %r", celery_exc)

    def _on_resend_verification(self, payload: EventPayload) -> None:
        from tuned.services.email_service import send_verification_email
        from tuned.utils.dependencies import get_services

        user_id   = payload.get("user_id")
        raw_token = payload.get("raw_token")

        try:
            user = get_services().user.get_user_obj(str(user_id))
            send_verification_email(user, str(raw_token or ""))
        except Exception as exc:
            logger.error(
                "[UserEventHandlers._on_resend_verification] Error: %r", exc
            )

    def _on_email_verified(self, payload: EventPayload) -> None:
        from tuned.tasks.notifications import create_in_app_notification
        from tuned.models.enums import NotificationType

        user_id = payload.get("user_id")
        create_in_app_notification.delay(
            user_id=str(user_id),
            title="Email Verified",
            message="Your email has been verified. Welcome to TunedEssays!",
            notification_type=NotificationType.SUCCESS.value,
        )

    def _on_password_changed(self, payload: EventPayload) -> None:
        from tuned.tasks.notifications import create_in_app_notification
        from tuned.models.enums import NotificationType

        user_id = payload.get("user_id")
        create_in_app_notification.delay(
            user_id=str(user_id),
            title="Password Changed",
            message=(
                "Your password has been successfully updated. "
                "If this wasn't you, please contact support immediately."
            ),
            notification_type=NotificationType.WARNING.value,
        )
