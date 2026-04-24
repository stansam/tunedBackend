from __future__ import annotations

import logging
from tuned.core.logging import get_logger
from tuned.tasks.payment_tasks import process_async_payment # generate_monthly_invoices
from flask_socketio import emit

logger: logging.Logger = get_logger(__name__)

class PaymentEventHandlers:
    def __init__(self, bus) -> None:
        self.bus = bus

    def register(self) -> None:
        self.bus.on("payment.created", self._on_payment_created)
        self.bus.on("payment.updated", self._on_payment_updated)
        self.bus.on("invoice.created", self._on_invoice_created)
        self.bus.on("refund.processed", self._on_refund_processed)
        logger.info("[PaymentEventHandlers] registered")

    def _on_payment_created(self, event_data: dict) -> None:
        try:
            logger.info(f"[PaymentEventHandlers] Processing payment.created: {event_data['payment_id']}")
            process_async_payment.delay(event_data['payment_id'])
            
            from tuned.extensions import socketio
            room = f"user_{event_data['user_id']}"
            socketio.emit("dashboard:payment_updated", {
                "payment_id": event_data["payment_id"],
                "status": event_data["status"]
            }, room=room)
        except Exception as exc:
            logger.error(f"[PaymentEventHandlers] Error in payment.created handler: {exc!r}")

    def _on_payment_updated(self, event_data: dict) -> None:
        try:
            logger.info(f"[PaymentEventHandlers] Processing payment.updated: {event_data['payment_id']}")
            
            from tuned.extensions import socketio
            room = f"user_{event_data['user_id']}"
            socketio.emit("dashboard:payment_updated", {
                "payment_id": event_data["payment_id"],
                "status": event_data["status"]
            }, room=room)
        except Exception as exc:
            logger.error(f"[PaymentEventHandlers] Error in payment.updated handler: {exc!r}")

    def _on_invoice_created(self, event_data: dict) -> None:
        try:
            logger.info(f"[PaymentEventHandlers] Processing invoice.created: {event_data['invoice_id']}")
            from tuned.repository import repositories
            from tuned.services.email_service import send_invoice_email
            
            invoice = repositories.payment.invoice.get_by_id(event_data['invoice_id'])
            user = repositories.user.get_user_by_id(event_data['user_id'])
            send_invoice_email(user, invoice)
        except Exception as exc:
            logger.error(f"[PaymentEventHandlers] Error in invoice.created handler: {exc!r}")

    def _on_refund_processed(self, event_data: dict) -> None:
        try:
            logger.info(f"[PaymentEventHandlers] Processing refund.processed: {event_data['refund_id']}")
            # TODO: Add email and dashboard notification
        except Exception as exc:
            logger.error(f"[PaymentEventHandlers] Error in refund.processed handler: {exc!r}")
