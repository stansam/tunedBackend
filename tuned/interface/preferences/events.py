import logging
from tuned.core.events import EventBus, EventPayload
from tuned.extensions import socketio
from tuned.core.logging import get_logger

logger: logging.Logger = get_logger(__name__)

class PreferenceEventHandlers:
    def __init__(self, bus: EventBus) -> None:
        self.bus = bus

    def register(self) -> None:
        self.bus.on("SETTINGS_UPDATED", self.handle_settings_updated)
        logger.debug("[PreferenceEventHandlers] Registered handlers.")

    def handle_settings_updated(self, payload: EventPayload) -> None:
        try:
            user_id = payload.get("user_id")
            category = payload.get("category")
            data = payload.get("payload")

            if not user_id:
                return

            room = f"user_{user_id}"
            logger.info(f"[Socket] Emitting settings_updated for user {user_id} in room {room}")
            
            socketio.emit(
                "settings_updated",
                {
                    "category": category,
                    "payload": data
                },
                room=room,
                namespace="/"
            )
        except Exception as e:
            logger.error(f"Error in handle_settings_updated: {str(e)}")
