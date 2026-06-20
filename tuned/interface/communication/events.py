from __future__ import annotations

import logging
from typing import Any
from tuned.core.events import EventBus, EventPayload
from tuned.core.logging import get_logger

logger: logging.Logger = get_logger(__name__)


class ChatEventHandlers:
    def __init__(self, event_bus: EventBus) -> None:
        self._bus = event_bus

    def register(self) -> None:
        self._bus.on("chat.message_sent", self._on_message_sent)
        logger.info("[ChatEventHandlers] registered")

    # TODO: Check on message interface and dms event handlers
    # TODO: Add logic for direct message delivery status (delivered/read)
    def _on_message_sent(self, payload: EventPayload) -> None:
        sender_id    = payload.get("sender_id")
        recipient_id = payload.get("recipient_id")
        chat_id      = payload.get("chat_id")
        message_id   = payload.get("message_id")
        content      = payload.get("content", "")
        is_admin     = payload.get("is_admin", False)
        created_at   = payload.get("created_at", "")

        socket_payload = {
            "chat_id":    str(chat_id),
            "message_id": str(message_id),
            "sender_id":  str(sender_id),
            "content":    content,
            "is_admin":   is_admin,
            "created_at": created_at,
        }

        try:
            from tuned.extensions import socketio
            # Emit to recipient
            if recipient_id:
                socketio.emit("chat:message", socket_payload, to=f"user_{recipient_id}")
            # Always inform admin room if message from client
            if not is_admin:
                socketio.emit("chat:message", socket_payload, to="admin_room")
        except Exception as exc:
            logger.error("[ChatEventHandlers._on_message_sent] Socket emit failed: %r", exc)

        # In-app notification for the recipient
        try:
            from tuned.tasks.notifications import create_in_app_notification
            if recipient_id:
                create_in_app_notification.delay(
                    user_id=str(recipient_id),
                    title="New Message",
                    message="You have a new message.",
                    notification_type="info",
                    action_url=f"/messages/{chat_id}",
                )
        except Exception as exc:
            logger.error("[ChatEventHandlers._on_message_sent] Notification failed: %r", exc)
