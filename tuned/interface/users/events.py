from __future__ import annotations

from tuned.core.events import EventBus, EventPayload
from tuned.core.logging import get_logger
import logging
from typing import cast, Any, Optional
from datetime import datetime, timezone

logger: logging.Logger = get_logger(__name__)


def get_country_code_from_ip(ip: str) -> Optional[str]:
    if not ip or ip in ("127.0.0.1", "localhost", "unknown"):
        return None
    try:
        import requests
        resp = requests.get(f"https://freeipapi.com/api/json/{ip}", timeout=3.0)
        if resp.status_code == 200:
            data = resp.json()
            cc = data.get("countryCode")
            if cc and len(cc) == 2:
                return cc.upper()
    except Exception as exc:
        logger.warning("[get_country_code_from_ip] Failed to lookup IP %s: %r", ip, exc)
    try:
        import requests
        resp = requests.get(f"http://ip-api.com/json/{ip}", timeout=3.0)
        if resp.status_code == 200:
            data = resp.json()
            cc = data.get("countryCode")
            if cc and len(cc) == 2:
                return cc.upper()
    except Exception as exc:
        logger.warning("[get_country_code_from_ip] Fallback failed for IP %s: %r", ip, exc)
    return None


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
        from tuned.dtos import LocalizationUpdateDTO
        from tuned.dtos.base import BaseRequestDTO

        user_id   = payload.get("user_id")
        raw_token = payload.get("raw_token")
        ip_address = payload.get("ip_address")

        try:
            # Initialize all user preference profiles
            if user_id is None:
                raise ValueError("user_id is required")
            services = get_services()
            services.user.init_user_preferences(str(user_id))

            # Geolocation logic
            if ip_address and ip_address not in ("127.0.0.1", "localhost", "unknown"):
                cc = get_country_code_from_ip(str(ip_address))
                if cc:
                    # loc_settings = db.session.query(UserLocalizationSettings).filter_by(user_id=user_id).first()
                    # if loc_settings:
                    #     loc_settings.country_code = cc
                    #     db.session.commit()
                    services.preferences.update_category(
                        "localization", str(user_id),
                        LocalizationUpdateDTO(country_code=cc), 
                        BaseRequestDTO(ip_address=ip_address)
                    )
                    # services.preferences._repo.save()

            # Socket notification to admin room
            try:
                from tuned.extensions import socketio
                socketio.emit(
                    "admin.user.registered",
                    {"user_id": str(user_id), "created_at": datetime.now(timezone.utc).isoformat()},
                    to="admin_room",
                )
            except Exception as socket_exc:
                logger.error("[UserEventHandlers._on_registered] Admin socket failed: %r", socket_exc)

            user = services.user._repo.get_user_by_id(str(user_id))
            send_verification_email(user, str(raw_token or ""))
            
            try:
                from tuned.tasks.email import send_welcome_task
                send_welcome_task.apply_async(
                    args=[user_id], countdown=1800, queue="email"
                )
            except Exception as celery_exc:
                logger.warning("[UserEventHandlers._on_registered] Celery welcome task failed/mocked: %r", celery_exc)
        except Exception as exc:
            logger.error("[UserEventHandlers._on_registered] Error: %r", exc)

    def _on_resend_verification(self, payload: EventPayload) -> None:
        from tuned.services.email_service import send_verification_email
        from tuned.utils.dependencies import get_services

        user_id   = payload.get("user_id")
        raw_token = payload.get("raw_token")

        try:
            user = get_services().user._repo.get_user_by_id(str(user_id))
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
            notification_type=NotificationType.SUCCESS,
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
            notification_type=NotificationType.WARNING,
        )
