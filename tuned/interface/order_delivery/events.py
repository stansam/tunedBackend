from __future__ import annotations

import logging
from tuned.core.events import EventBus, EventPayload
from tuned.core.logging import get_logger

logger: logging.Logger = get_logger(__name__)

class OrderDeliveryEventHandlers:
    def __init__(self, event_bus: EventBus) -> None:
        self._bus = event_bus

    def register(self) -> None:
        self._bus.on("delivery.created", self._on_created)
        self._bus.on("delivery.status_changed", self._on_status_changed)
        self._bus.on("delivery.files_added", self._on_files_added)
        self._bus.on("delivery.deleted", self._on_deleted)
        logger.info("[OrderDeliveryEventHandlers] registered")

    def _on_created(self, payload: EventPayload) -> None:
        client_id = payload.get("client_id")
        order_number = payload.get("order_number", "")
        delivery_resp = payload.get("delivery")

        try:
            from tuned.extensions import socketio
            socketio.emit(
                "order:delivery:created",
                delivery_resp,
                to=f"user_{client_id}",
            )
        except Exception as exc:
            logger.error(
                "[OrderDeliveryEventHandlers._on_created] Socket emit failed: %r", exc
            )

        try:
            from tuned.tasks.notifications import create_in_app_notification
            from tuned.models.enums import NotificationType
            create_in_app_notification.delay(
                user_id=str(client_id),
                title="Order Delivered",
                message=f"Order {order_number} has been delivered successfully. Please review the files.",
                notification_type=NotificationType.SUCCESS.value.upper(),
            )
        except Exception as exc:
            logger.error(
                "[OrderDeliveryEventHandlers._on_created] Notification task failed: %r", exc
            )

    def _on_status_changed(self, payload: EventPayload) -> None:
        client_id = payload.get("client_id")
        delivery_resp = payload.get("delivery")
        
        try:
            from tuned.extensions import socketio
            socketio.emit(
                "order:delivery:updated",
                delivery_resp,
                to=f"user_{client_id}",
            )
        except Exception as exc:
            logger.error(
                "[OrderDeliveryEventHandlers._on_status_changed] Socket emit failed: %r", exc
            )

    def _on_files_added(self, payload: EventPayload) -> None:
        client_id = payload.get("client_id")
        delivery_resp = payload.get("delivery")

        try:
            from tuned.extensions import socketio
            socketio.emit(
                "order:delivery:updated",
                delivery_resp,
                to=f"user_{client_id}",
            )
        except Exception as exc:
            logger.error(
                "[OrderDeliveryEventHandlers._on_files_added] Socket emit failed: %r", exc
            )

    def _on_deleted(self, payload: EventPayload) -> None:
        client_id = payload.get("client_id")
        delivery_id = payload.get("delivery_id")

        try:
            from tuned.extensions import socketio
            socketio.emit(
                "order:delivery:deleted",
                {"id": delivery_id},
                to=f"user_{client_id}",
            )
        except Exception as exc:
            logger.error(
                "[OrderDeliveryEventHandlers._on_deleted] Socket emit failed: %r", exc
            )
