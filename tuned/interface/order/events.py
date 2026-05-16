from __future__ import annotations

import logging
from tuned.core.events import EventBus, EventPayload
from tuned.core.logging import get_logger

logger: logging.Logger = get_logger(__name__)


class OrderEventHandlers:
    def __init__(self, event_bus: EventBus) -> None:
        self._bus = event_bus

    def register(self) -> None:
        self._bus.on("order.status_changed", self._on_status_changed)
        self._bus.on("order.created",        self._on_created)
        self._bus.on("order.draft_saved",    self._on_draft_saved)
        self._bus.on("order.comment", self._on_comment_created)
        self._bus.on("order.comment.updated", self._on_comment_updated)
        self._bus.on("order.comment.deleted", self._on_comment_deleted)
        logger.info("[OrderEventHandlers] registered")

    def _on_status_changed(self, payload: EventPayload) -> None:
        order_id    = payload.get("order_id")
        client_id   = payload.get("client_id")
        new_status  = payload.get("new_status", "")
        progress    = payload.get("progress", 0)
        delivered_at = payload.get("delivered_at")
        order_number = payload.get("order_number", "")
        try:
            from tuned.extensions import socketio
            socketio.emit(
                "order.updated",
                {
                    "id":           str(order_id),
                    "order_number": order_number,
                    "status":       new_status,
                    "progress":     progress,
                    "delivered_at": delivered_at,
                },
                to=f"user_{client_id}",
            )
        except Exception as exc:
            logger.error(
                "[OrderEventHandlers._on_status_changed] Socket emit failed: %r", exc
            )
        try:
            from tuned.tasks.notifications import create_in_app_notification
            from tuned.models.enums import NotificationType
            create_in_app_notification.delay(
                user_id=str(client_id),
                title="Order Updated",
                message=f"Order {order_number} status changed to {new_status}.",
                notification_type=NotificationType.INFO.value.upper(),
            )
        except Exception as exc:
            logger.error(
                "[OrderEventHandlers._on_status_changed] Notification task failed: %r",
                exc,
            )

        try:
            from tuned.utils.dependencies import get_services
            from tuned.dtos.audit import OrderStatusHistoryCreateDTO
            services = get_services()
            services.audit.order_status_history.log_status_change(OrderStatusHistoryCreateDTO(
                order_id=str(order_id),
                user_id=str(client_id),
                old_status=payload.get("old_status"),
                new_status=new_status,
            ))
        except Exception as exc:
            logger.error(
                "[OrderEventHandlers._on_status_changed] Audit failed: %r", exc
            )

    def _on_created(self, payload: EventPayload) -> None:
        client_id    = payload.get("client_id")
        order_number = payload.get("order_number", "")

        try:
            from tuned.tasks.notifications import create_in_app_notification
            from tuned.models.enums import NotificationType
            create_in_app_notification.delay(
                user_id=str(client_id),
                title="New Order Placed",
                message=f"Order {order_number} has been created successfully.",
                notification_type=NotificationType.SUCCESS.value.upper(),
            )
        except Exception as exc:
            logger.error(
                "[OrderEventHandlers._on_created] Notification task failed: %r", exc
            )

    def _on_draft_saved(self, payload: EventPayload) -> None:
        user_id  = payload.get("user_id")
        order_id = payload.get("order_id", "")

        try:
            from tuned.extensions import socketio
            socketio.emit("order.draft_saved", {"draft_id": str(order_id)}, to=f"user_{user_id}")
        except Exception as exc:
            logger.error(
                "[OrderEventHandlers._on_draft_saved] Socket emit failed: %r", exc
            )
    
    def _on_comment_created(self, payload: EventPayload) -> None:
        result   = payload.get("result")
        order_id  = payload.get("order_id")
        try:
            from tuned.extensions import socketio
            socketio.emit(
                "order:comment",
                result,
                to=f"order_{order_id}",
            )
        except Exception as exc:
            logger.error(
                "[OrderEventHandlers._on_comment_updated] Socket emit failed: %r", exc
            )
    
    def _on_comment_updated(self, payload: EventPayload) -> None:
        result = payload.get("result")
        order_id   = payload.get("order_id")
        try:
            from tuned.extensions import socketio
            socketio.emit(
                "order:comment:updated",
                result,
                to=f"order_{order_id}",
            )
        except Exception as exc:
            logger.error(
                "[OrderEventHandlers._on_comment_updated] Socket emit failed: %r", exc
            )
    
    def _on_comment_deleted(self, payload: EventPayload) -> None:
        comment_id   = payload.get("comment_id")
        order_id   = payload.get("order_id")
        try:
            from tuned.extensions import socketio
            socketio.emit(
                "order:comment:deleted",
                {"comment_id": comment_id},
                to=f"order_{order_id}",
            )
        except Exception as exc:
            logger.error(
                "[OrderEventHandlers._on_comment_deleted] Socket emit failed: %r", exc
            )
