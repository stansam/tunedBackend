from __future__ import annotations

import logging
from tuned.core.logging import get_logger

logger: logging.Logger = get_logger(__name__)


class EventRegistry:
    def __init__(self) -> None:
        self._registered = False

    def register_all(self) -> None:
        if self._registered:
            logger.debug("[EventRegistry] Already registered — skipping.")
            return

        from tuned.core.events import get_event_bus
        bus = get_event_bus()

        from tuned.interface.users.events import UserEventHandlers
        from tuned.interface.order.events import OrderEventHandlers

        UserEventHandlers(bus).register()
        OrderEventHandlers(bus).register()

        self._registered = True
        logger.info("[EventRegistry] All domain handlers registered.")


_registry: EventRegistry | None = None


def _get_registry() -> EventRegistry:
    global _registry
    if _registry is None:
        _registry = EventRegistry()
    return _registry


def register_all_handlers() -> None:
    _get_registry().register_all()
