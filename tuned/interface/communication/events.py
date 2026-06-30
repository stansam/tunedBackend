from __future__ import annotations

import logging
from typing import Any
from tuned.core.events import EventBus, EventPayload
from tuned.core.logging import get_logger

logger: logging.Logger = get_logger(__name__)
class ChatEvents:
    MESSAGE_SENT = "chat.message_sent"
    CHAT_CREATED = "chat.created"
    STATUS_CHANGED = "chat.status_changed"
    ASSIGNED = "chat.assigned"
    MESSAGE_READ = "chat.message_read"
    MESSAGE_EDITED = "chat.message_edited"
    MESSAGE_DELETED = "chat.message_deleted"

class ChatEventHandlers:
    def __init__(self, event_bus: EventBus) -> None:
        self._bus = event_bus

    def register(self) -> None:
        self._bus.on(ChatEvents.MESSAGE_SENT, self._on_message_sent)
        self._bus.on(ChatEvents.CHAT_CREATED, self._on_chat_created)
        self._bus.on(ChatEvents.STATUS_CHANGED, self._on_chat_status_changed)
        self._bus.on(ChatEvents.ASSIGNED, self._on_chat_assigned)
        self._bus.on(ChatEvents.MESSAGE_READ, self._on_message_read)
        self._bus.on(ChatEvents.MESSAGE_EDITED, self._on_message_edited)
        self._bus.on(ChatEvents.MESSAGE_DELETED, self._on_message_deleted)
        logger.info("[ChatEventHandlers] registered")

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
            # Broadcast to the active chat room
            socketio.emit("chat:message", socket_payload, to=f"chat_{chat_id}")
            # Inform admin room for new message notifications/counters if message is from client
            if not is_admin:
                socketio.emit("chat:message", socket_payload, to="admin_room")
            else:
                # Inform the specific recipient's room for badge updates
                if recipient_id:
                    socketio.emit("chat:message", socket_payload, to=f"user_{recipient_id}")
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

    def _on_chat_created(self, payload: EventPayload) -> None:
        chat_id = payload.get("chat_id")
        user_id = payload.get("user_id")
        subject = payload.get("subject")
        order_id = payload.get("order_id")
        created_at = payload.get("created_at")

        socket_payload = {
            "chat_id": str(chat_id),
            "user_id": str(user_id),
            "subject": subject,
            "order_id": str(order_id) if order_id else None,
            "created_at": created_at
        }

        try:
            from tuned.extensions import socketio
            # Notify admins of new chat
            socketio.emit("admin:chat:created", socket_payload, to="admin_room")
        except Exception as exc:
            logger.error("[ChatEventHandlers._on_chat_created] Socket emit failed: %r", exc)

    def _on_chat_status_changed(self, payload: EventPayload) -> None:
        chat_id = payload.get("chat_id")
        user_id = payload.get("user_id")
        new_status = payload.get("new_status")
        old_status = payload.get("old_status")
        changed_by = payload.get("changed_by")

        socket_payload = {
            "chat_id": str(chat_id),
            "status": new_status,
            "old_status": old_status,
            "changed_by": str(changed_by)
        }

        try:
            from tuned.extensions import socketio
            socketio.emit("chat:status_changed", socket_payload, to=f"chat_{chat_id}")
            socketio.emit("chat:status_changed", socket_payload, to=f"user_{user_id}")
            socketio.emit("chat:status_changed", socket_payload, to="admin_room")
        except Exception as exc:
            logger.error("[ChatEventHandlers._on_chat_status_changed] Socket emit failed: %r", exc)

    def _on_chat_assigned(self, payload: EventPayload) -> None:
        chat_id = payload.get("chat_id")
        user_id = payload.get("user_id")
        admin_id = payload.get("admin_id")
        assigned_by = payload.get("assigned_by")

        socket_payload = {
            "chat_id": str(chat_id),
            "admin_id": str(admin_id),
            "assigned_by": str(assigned_by)
        }

        try:
            from tuned.extensions import socketio
            socketio.emit("chat:assigned", socket_payload, to=f"chat_{chat_id}")
            socketio.emit("chat:assigned", socket_payload, to=f"user_{user_id}")
            socketio.emit("chat:assigned", socket_payload, to="admin_room")
        except Exception as exc:
            logger.error("[ChatEventHandlers._on_chat_assigned] Socket emit failed: %r", exc)

    def _on_message_read(self, payload: EventPayload) -> None:
        chat_id = payload.get("chat_id")
        reader_id = payload.get("reader_id")
        recipient_id = payload.get("recipient_id")
        message_ids = payload.get("message_ids", [])

        socket_payload = {
            "chat_id": str(chat_id),
            "reader_id": str(reader_id),
            "message_ids": [str(m) for m in message_ids]
        }

        try:
            from tuned.extensions import socketio
            socketio.emit("chat:read", socket_payload, to=f"chat_{chat_id}")
        except Exception as exc:
            logger.error("[ChatEventHandlers._on_message_read] Socket emit failed: %r", exc)

    def _on_message_edited(self, payload: EventPayload) -> None:
        chat_id = payload.get("chat_id")
        message_id = payload.get("message_id")
        recipient_id = payload.get("recipient_id")
        content = payload.get("content", "")
        updated_at = payload.get("updated_at", "")

        socket_payload = {
            "chat_id": str(chat_id),
            "message_id": str(message_id),
            "content": content,
            "is_edited": True,
            "updated_at": updated_at
        }

        try:
            from tuned.extensions import socketio
            socketio.emit("chat:message:updated", socket_payload, to=f"chat_{chat_id}")
        except Exception as exc:
            logger.error("[ChatEventHandlers._on_message_edited] Socket emit failed: %r", exc)

    def _on_message_deleted(self, payload: EventPayload) -> None:
        chat_id = payload.get("chat_id")
        message_id = payload.get("message_id")
        recipient_id = payload.get("recipient_id")

        socket_payload = {
            "chat_id": str(chat_id),
            "message_id": str(message_id),
            "is_deleted": True
        }

        try:
            from tuned.extensions import socketio
            socketio.emit("chat:message:deleted", socket_payload, to=f"chat_{chat_id}")
        except Exception as exc:
            logger.error("[ChatEventHandlers._on_message_deleted] Socket emit failed: %r", exc)
