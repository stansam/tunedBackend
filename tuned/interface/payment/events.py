from __future__ import annotations

import logging
from typing import Any, Dict, TYPE_CHECKING
from tuned.core.logging import get_logger

if TYPE_CHECKING:
    from tuned.core.events import EventBus

logger: logging.Logger = get_logger(__name__)

class PaymentEventHandlers:
    def __init__(self, bus: EventBus) -> None:
        self.bus = bus

    def register(self) -> None:
        self.bus.on("payment.created", self._on_payment_created)
        self.bus.on("payment.client_marked_paid", self._on_payment_client_marked_paid)
        self.bus.on("payment.verified_by_admin", self._on_payment_verified_by_admin)
        self.bus.on("invoice.created", self._on_invoice_created)
        self.bus.on("refund.processed", self._on_refund_processed)
        logger.info("[PaymentEventHandlers] registered")

    def _on_payment_created(self, event_data: Dict[str, Any]) -> None:
        try:
            logger.info(f"[PaymentEventHandlers] Processing payment.created: {event_data['payment_id']}")
            from tuned.extensions import socketio
            room = f"user_{event_data['user_id']}"
            socketio.emit("dashboard:payment_updated", {
                "payment_id": event_data["payment_id"],
                "status": event_data["status"]
            }, room=room)
        except Exception as exc:
            logger.error(f"[PaymentEventHandlers] Error in payment.created handler: {exc!r}")

    def _on_payment_client_marked_paid(self, event_data: Dict[str, Any]) -> None:
        try:
            logger.info(f"[PaymentEventHandlers] Processing payment.client_marked_paid: {event_data['payment_id']}")
            # TODO: Notify Admin (log actionable alert)
            # from tuned.interface.notifications import notification_service
            # notification_service.create_admin_alert("Payment marked paid, pending verification")
            
            from tuned.extensions import socketio
            room = f"user_{event_data['user_id']}"
            socketio.emit("dashboard:payment_updated", { # TODO: Implement SocketIO Event handler
                "payment_id": event_data["payment_id"],
                "status": event_data["status"]
            }, room=room)
        except Exception as exc:
            logger.error(f"[PaymentEventHandlers] Error in payment.client_marked_paid handler: {exc!r}")

    def _on_payment_verified_by_admin(self, event_data: Dict[str, Any]) -> None:
        try:
            logger.info(f"[PaymentEventHandlers] Processing payment.verified_by_admin: {event_data['payment_id']}")
            from tuned.extensions import socketio
            room = f"user_{event_data['user_id']}"
            socketio.emit("dashboard:payment_updated", { # TODO: Implement SocketIO Event handler
                "payment_id": event_data["payment_id"],
                "status": event_data["status"]
            }, room=room)
        except Exception as exc:
            logger.error(f"[PaymentEventHandlers] Error in payment.verified_by_admin handler: {exc!r}")

    def _on_invoice_created(self, event_data: Dict[str, Any]) -> None:
        try:
            logger.info(f"[PaymentEventHandlers] Processing invoice.created: {event_data['invoice_id']}")
            from tuned.utils.dependencies import get_services
            from tuned.services.email_service import send_invoice_email
            
            services = get_services()
            invoice = services.payment.invoice.get_details(event_data['invoice_id'])
            user = services._repos.user.get_user_by_id(event_data['user_id'])
            send_invoice_email(user, invoice)
        except Exception as exc:
            logger.error(f"[PaymentEventHandlers] Error in invoice.created handler: {exc!r}")

    def _on_refund_processed(self, event_data: Dict[str, Any]) -> None:
        try:
            logger.info(f"[PaymentEventHandlers] Processing refund.processed: {event_data['refund_id']}")
            # TODO: Add email and dashboard notification
        except Exception as exc:
            logger.error(f"[PaymentEventHandlers] Error in refund.processed handler: {exc!r}")
