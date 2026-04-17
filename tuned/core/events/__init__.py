from __future__ import annotations
from typing import Any, Callable, Dict, List
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

EventPayload = Dict[str, Any]
EventHandler = Callable[[EventPayload], None]

class EventBus:
    def __init__(self) -> None:
        self._handlers: Dict[str, List[EventHandler]] = defaultdict(list)

    def on(self, event: str, handler: EventHandler) -> None:
        if handler not in self._handlers[event]: 
            self._handlers[event].append(handler)
            logger.debug(f"[EventBus] Registered handler '{handler.__name__}' for '{event}'")
        else:
            logger.debug(f"[EventBus] Handler '{handler.__name__}' already registered for '{event}'")

    def emit(self, event: str, payload: EventPayload) -> None:
        handlers = self._handlers.get(event, [])
        if not handlers:
            logger.debug(f"[EventBus] No handlers for event '{event}'")
            return

        for handler in handlers:
            try:
                logger.debug(f"[EventBus] Emitting '{event}' to {len(handlers)} handlers (instance={id(self)})")
                handler(payload)
            except Exception as exc:
                logger.error(
                    f"[EventBus] Handler '{handler.__name__}' for '{event}' raised: {exc!r}",
                    exc_info=True,
                )

    def off(self, event: str, handler: EventHandler) -> None:
        handlers = self._handlers.get(event, [])
        self._handlers[event] = [h for h in handlers if h is not handler]

_event_bus: EventBus | None = None

def get_event_bus() -> EventBus:
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus

# event_bus = get_event_bus()
