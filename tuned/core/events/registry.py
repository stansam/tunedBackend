from __future__ import annotations

import logging
from tuned.core.logging import get_logger

logger: logging.Logger = get_logger(__name__)


class EventRegistry:
    def register_all(self) -> None:
        from tuned.core.events import get_event_bus
        bus = get_event_bus()

        from tuned.interface.users.events import UserEventHandlers
        from tuned.interface.order.events import OrderEventHandlers
        from tuned.interface.preferences.events import PreferenceEventHandlers
        from tuned.interface.payment.events import PaymentEventHandlers
        from tuned.interface.referral.events import ReferralEventHandlers
        from tuned.interface.order_delivery.events import OrderDeliveryEventHandlers
        from tuned.interface.communication.events import ChatEventHandlers
        from tuned.interface.content.events import ContentEventHandlers

        UserEventHandlers(bus).register()
        OrderEventHandlers(bus).register()
        PreferenceEventHandlers(bus).register()
        PaymentEventHandlers(bus).register()
        ReferralEventHandlers(bus).register()
        OrderDeliveryEventHandlers(bus).register()
        ChatEventHandlers(bus).register()
        ContentEventHandlers(bus).register()

        logger.info("[EventRegistry] All domain handlers registered.")


_registry: EventRegistry | None = None


def _get_registry() -> EventRegistry:
    global _registry
    if _registry is None:
        _registry = EventRegistry()
    return _registry


def register_all_handlers() -> None:
    _get_registry().register_all()
