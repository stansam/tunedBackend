from __future__ import annotations
from typing import Any, Callable, Dict, List
from collections import defaultdict
import logging
import threading

logger = logging.getLogger(__name__)

EventPayload = Dict[str, Any]
EventHandler = Callable[[EventPayload], None]

class EventBus:
    def __init__(self) -> None:
        self._handlers: Dict[str, List[EventHandler]] = defaultdict(list)
        self._lock = threading.RLock()

    def on(self, event: str, handler: EventHandler) -> None:
        with self._lock:
            if handler not in self._handlers[event]: 
                self._handlers[event].append(handler)
                logger.debug("[EventBus] Registered handler '%s' for '%s'", handler.__name__, event)
            else:
                logger.debug("[EventBus] Handler '%s' already registered for '%s'", handler.__name__, event)

    def emit(self, event: str, payload: EventPayload) -> None:
        with self._lock:
            handlers = list(self._handlers.get(event, []))
        if not handlers:
            logger.debug("[EventBus] No handlers for event '%s'", event)
            return

        logger.debug("[EventBus] Emitting '%s' to %d handlers (instance=%d)", event, len(handlers), id(self))
        for handler in handlers:
            try:
                handler(payload)
            except Exception as exc:
                logger.error(
                    "[EventBus] Handler '%s' for '%s' raised: %r",
                    handler.__name__,
                    event,
                    exc,
                    exc_info=True,
                )

    def off(self, event: str, handler: EventHandler) -> None:
        with self._lock:
            handlers = self._handlers.get(event, [])
            self._handlers[event] = [h for h in handlers if h is not handler]

_event_bus: EventBus | None = None

def get_event_bus() -> EventBus:
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus


