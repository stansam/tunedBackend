import logging
from tuned.core.events import EventBus, EventPayload
from tuned.core.logging import get_logger

logger: logging.Logger = get_logger(__name__)

class PreferenceEventHandlers:
    def __init__(self, bus: EventBus) -> None:
        self._bus = bus
        self._bus = bus

    def register(self) -> None:
        self._bus.on("preferences.settings_updated", self.handle_settings_updated)
        self._bus.on("preferences.settings_updated", self.handle_settings_updated)
        logger.debug("[PreferenceEventHandlers] Registered handlers.")

    def handle_settings_updated(self, payload: EventPayload) -> None:
        try:
            user_id = payload.get("user_id")
            category = payload.get("category")
            data = payload.get("payload")

            if not user_id:
                return

            room = f"user_{user_id}"
            logger.info("[Socket] Emitting preferences:updated for user %s in room %s", user_id, room)
            logger.info("[Socket] Emitting preferences:updated for user %s in room %s", user_id, room)
            
            from tuned.extensions import socketio
            from tuned.extensions import socketio
            socketio.emit(
                "preferences:updated",
                "preferences:updated",
                {
                    "category": category,
                    "payload": data
                },
                to=room
            )
        except Exception as e:
            logger.error("Error in handle_settings_updated: %r", e)
            logger.error("Error in handle_settings_updated: %r", e)
