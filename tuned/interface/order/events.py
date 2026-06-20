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
        self._bus.on("order.revision_requested",      self._on_revision_requested)
        self._bus.on("order.revision_status_changed", self._on_revision_status_changed)
        self._bus.on("order.deadline_extension_requested", self._on_deadline_extension_requested)
        self._bus.on("order.deadline_extension_responded", self._on_deadline_extension_responded)
        self._bus.on("order.admin.escalated", self._on_admin_order_escalated)
        logger.info("[OrderEventHandlers] registered")

    def _on_status_changed(self, payload: EventPayload) -> None:
        order_id     = payload.get("order_id")
        client_id    = payload.get("client_id")
        new_status   = payload.get("new_status", "")
        progress     = payload.get("progress", 0)
        order_id     = payload.get("order_id")
        client_id    = payload.get("client_id")
        new_status   = payload.get("new_status", "")
        progress     = payload.get("progress", 0)
        delivered_at = payload.get("delivered_at")
        order_number = payload.get("order_number", "")
        title        = payload.get("title", "")
        due_date     = payload.get("due_date")

        title        = payload.get("title", "")
        due_date     = payload.get("due_date")

        try:
            from tuned.extensions import socketio
            socketio.emit(
                "order:updated",
                "order:updated",
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

        # Notify admins
        try:
            from tuned.extensions import socketio
            from tuned.dtos.order import derive_priority
            from datetime import datetime

            if isinstance(due_date, datetime):
                due = due_date
                due_str = due.isoformat()
            elif due_date:
                due = datetime.fromisoformat(due_date)
                due_str = due_date
            else:
                due = None
                due_str = ""

            socketio.emit(
                "admin:order:status_changed",
                {
                    "id":           str(order_id),
                    "order_number": order_number,
                    "title":        title,
                    "due_date":     due_str,
                    "priority":     derive_priority(due).name if due else "NORMAL",
                },
                to="admin_room",
            )
        except Exception as exc:
            logger.error(
                "[OrderEventHandlers._on_status_changed] Admin socket emit failed: %r", exc
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

        # Notify admins
        try:
            from tuned.extensions import socketio
            socketio.emit(
                "admin:order:created",
                {
                    "order_number": order_number,
                    "client_id":    str(client_id),
                },
                to="admin_room",
            )
        except Exception as exc:
            logger.error(
                "[OrderEventHandlers._on_created] Admin socket emit failed: %r", exc
            )


    def _on_draft_saved(self, payload: EventPayload) -> None:
        user_id  = payload.get("user_id")
        order_id = payload.get("order_id", "")

        try:
            from tuned.extensions import socketio
            socketio.emit("order:draft_saved", {"draft_id": str(order_id)}, to=f"user_{user_id}")
        except Exception as exc:
            logger.error(
                "[OrderEventHandlers._on_draft_saved] Socket emit failed: %r", exc
            )
    
    def _on_comment_created(self, payload: EventPayload) -> None:
        result   = payload.get("result")
        order_id  = payload.get("order_id")
        try:
            from tuned.extensions import socketio
            from tuned.utils.socket_payload import safe_payload
            socketio.emit(
                "order:comment",
                safe_payload(result),
                to=f"order_{order_id}",
            )
        except Exception as exc:
            logger.error(
                "[OrderEventHandlers._on_comment_created] Socket emit failed: %r", exc
            )
    
    def _on_comment_updated(self, payload: EventPayload) -> None:
        result = payload.get("result")
        order_id   = payload.get("order_id")
        try:
            from tuned.extensions import socketio
            from tuned.utils.socket_payload import safe_payload
            socketio.emit(
                "order:comment:updated",
                safe_payload(result),
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
            from tuned.utils.socket_payload import safe_payload
            socketio.emit(
                "order:comment:deleted",
                safe_payload({"comment_id": comment_id}),
                to=f"order_{order_id}",
            )
        except Exception as exc:
            logger.error(
                "[OrderEventHandlers._on_comment_deleted] Socket emit failed: %r", exc
            )

    def _on_revision_requested(self, payload: EventPayload) -> None:
        order_number = payload.get("order_number", "")
        order_id     = payload.get("order_id")
        client_id    = payload.get("client_id")
        revision_id  = payload.get("revision_id")

        try:
            from tuned.extensions import socketio
            socketio.emit("admin:revision:requested", {
                "order_id":     str(order_id),
                "order_number": order_number,
                "revision_id":  str(revision_id),
            }, to="admin_room")
        except Exception as exc:
            logger.error("[OrderEventHandlers._on_revision_requested] Admin socket failed: %r", exc)

    def _on_revision_status_changed(self, payload: EventPayload) -> None:
        client_id    = payload.get("client_id")
        order_number = payload.get("order_number", "")
        new_status   = payload.get("new_status", "")
        order_id     = payload.get("order_id")
        revision_id  = payload.get("revision_id")

        try:
            from tuned.extensions import socketio
            socketio.emit("order:revision:status_changed", {
                "order_id":    str(order_id),
                "revision_id": str(revision_id),
                "new_status":  new_status,
            }, to=f"user_{client_id}")
            socketio.emit("order:revision:status_changed", {
                "order_id":    str(order_id),
                "revision_id": str(revision_id),
                "new_status":  new_status,
            }, to=f"order_{order_id}")
        except Exception as exc:
            logger.error("[OrderEventHandlers._on_revision_status_changed] Socket failed: %r", exc)

        try:
            from tuned.tasks.notifications import create_in_app_notification
            status_messages = {
                "in_progress": f"Your revision request for Order {order_number} is being worked on.",
                "completed":   f"Revision for Order {order_number} is complete. A new delivery has been made.",
                "rejected":    f"Your revision request for Order {order_number} was rejected. Please contact support.",
                "cancelled":   f"Revision request for Order {order_number} has been cancelled.",
            }
            message = status_messages.get(new_status, f"Revision status for Order {order_number} changed to {new_status}.")
            create_in_app_notification.delay(
                user_id=str(client_id),
                title="Revision Request Updated",
                message=message,
                notification_type="info",
                action_url=f"/client/orders/{order_number}",
            )
        except Exception as exc:
            logger.error("[OrderEventHandlers._on_revision_status_changed] Notification failed: %r", exc)

    def _on_deadline_extension_requested(self, payload: EventPayload) -> None:
        client_id       = payload.get("client_id")
        order_id        = payload.get("order_id")
        order_number    = payload.get("order_number", "")
        requested_hours = payload.get("requested_hours", 0)
        extension_id    = payload.get("extension_id", "")

        try:
            import uuid
            from tuned.tasks.dashboard_tasks import emit_actionable_alert
            from tuned.models.enums import ActionableAlertType
            emit_actionable_alert.delay(
                client_id=str(client_id),
                alert_id=str(uuid.uuid4()),
                alert_type=ActionableAlertType.EXTENSION_REQUEST.value,
                message=f"Admin has requested a {requested_hours}h deadline extension for Order {order_number}.",
                metadata={
                    "order_id":       str(order_id),
                    "order_number":   order_number,
                    "extension_id":   str(extension_id),
                    "requested_hours": requested_hours,
                },
            )
        except Exception as exc:
            logger.error("[OrderEventHandlers._on_deadline_extension_requested] Alert failed: %r", exc)

        try:
            from tuned.tasks.notifications import create_in_app_notification
            create_in_app_notification.delay(
                user_id=str(client_id),
                title="Deadline Extension Requested",
                message=f"Admin is requesting a {requested_hours}h extension for Order {order_number}. Please review.",
                notification_type="warning",
                action_url=f"/client/orders/{order_number}",
            )
        except Exception as exc:
            logger.error("[OrderEventHandlers._on_deadline_extension_requested] Notification failed: %r", exc)

    def _on_deadline_extension_responded(self, payload: EventPayload) -> None:
        admin_id     = payload.get("admin_id")
        order_number = payload.get("order_number", "")
        client_name  = payload.get("client_name", "")
        response     = payload.get("response", "")
        order_id     = payload.get("order_id")

        try:
            from tuned.extensions import socketio
            socketio.emit("admin:order:extension_responded", {
                "order_id":     str(order_id),
                "order_number": order_number,
                "response":     response,
            }, to="admin_room")
        except Exception as exc:
            logger.error("[OrderEventHandlers._on_deadline_extension_responded] Socket failed: %r", exc)

        try:
            from tuned.tasks.notifications import create_in_app_notification
            msg = (
                f"Client {client_name} approved the deadline extension for Order {order_number}."
                if response == "approved"
                else f"Client {client_name} rejected the deadline extension for Order {order_number}."
            )
            if admin_id:
                create_in_app_notification.delay(
                    user_id=str(admin_id),
                    title="Deadline Extension Response",
                    message=msg,
                    notification_type="success" if response == "approved" else "warning",
                    action_url=f"/admin/orders/{order_number}",
                )
        except Exception as exc:
            logger.error("[OrderEventHandlers._on_deadline_extension_responded] Notification failed: %r", exc)

    def _on_admin_order_escalated(self, payload: EventPayload) -> None:
        order_id     = payload.get("order_id")
        order_number = payload.get("order_number", "")

        try:
            from tuned.extensions import socketio
            socketio.emit("admin:order:escalated", {
                "order_id":     str(order_id),
                "order_number": order_number,
            }, to="admin_room")
        except Exception as exc:
            logger.error("[OrderEventHandlers._on_admin_order_escalated] Socket failed: %r", exc)
