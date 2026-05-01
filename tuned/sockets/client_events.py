from __future__ import annotations

from flask_login import current_user
from flask_socketio import join_room # leave_room

from tuned.core.logging import get_logger
import logging
from typing import Any

logger: logging.Logger = get_logger(__name__)

class ClientSocketHandler:
    def register(self, socketio: Any) -> None:
        socketio.on_event("dashboard:subscribe",   self._on_subscribe)
        socketio.on_event("dashboard:unsubscribe", self._on_unsubscribe)
        logger.info("[ClientSocketHandler] dashboard events registered")

    def _on_subscribe(self, data: dict[str, Any]) -> None:
        if not current_user or not current_user.is_authenticated:
            logger.warning("[ClientSocketHandler] Unauthenticated subscribe attempt")
            return
        room = f"user_{current_user.id}"
        join_room(room)
        logger.debug("[ClientSocketHandler] User %s active for dashboard in %s", current_user.id, room)

    def _on_unsubscribe(self, data: dict[str, Any]) -> None:
        # if not current_user or not current_user.is_authenticated:
        #     return
        # room = f"user_{current_user.id}"
        # leave_room(room)
        # logger.debug("[ClientSocketHandler] User %s unsubscribed from %s", current_user.id, room)
        logger.debug("[ClientSocketHandler] User %s dashboard subscription deactivated", current_user.id)

def _register_client_events() -> None:
    try:
        from tuned.extensions import socketio
        ClientSocketHandler().register(socketio)
    except Exception as exc:
        logger.error("[ClientSocketHandler] Registration failed: %r", exc)


_register_client_events()
