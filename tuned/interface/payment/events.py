from __future__ import annotations

import logging
from typing import Any, Dict, TYPE_CHECKING
from tuned.core.logging import get_logger

if TYPE_CHECKING:
    from tuned.core.events import EventBus

logger: logging.Logger = get_logger(__name__)



class PaymentEventHandlers:
    def __init__(self, bus: EventBus) -> None:
        self._bus = bus
        self._bus = bus

    def register(self) -> None:
        self._bus.on("payment.created", self._on_payment_created)
        self._bus.on("payment.client_marked_paid", self._on_payment_client_marked_paid)
        self._bus.on("payment.verified_by_admin", self._on_payment_verified_by_admin)
        self._bus.on("invoice.created", self._on_invoice_created)
        self._bus.on("refund.processed", self._on_refund_processed)
        self._bus.on("payment.marked_failed", self._on_marked_failed)
        logger.info("[PaymentEventHandlers] registered")

    def _on_payment_created(self, event_data: Dict[str, Any]) -> None:
        try:
            logger.info("[PaymentEventHandlers] Processing payment.created: %s", event_data.get("payment_id"))
            logger.info("[PaymentEventHandlers] Processing payment.created: %s", event_data.get("payment_id"))
            from tuned.extensions import socketio
            room = f"user_{event_data.get('user_id')}"
            room = f"user_{event_data.get('user_id')}"
            socketio.emit("dashboard:payment_updated", {
                "payment_id": str(event_data.get("payment_id")),
                "status": event_data.get("status")
            }, to=room)
        except Exception as exc:
            logger.error("[PaymentEventHandlers] Error in payment.created handler: %r", exc)
            logger.error("[PaymentEventHandlers] Error in payment.created handler: %r", exc)

    def _on_payment_client_marked_paid(self, event_data: Dict[str, Any]) -> None:
        try:
            logger.info("[PaymentEventHandlers] Processing payment.client_marked_paid: %s", event_data.get("payment_id"))
            from tuned.tasks.notifications import create_in_app_notification
            from tuned.extensions import socketio

            user_id = event_data.get("user_id")
            order_number = event_data.get("order_number")
            client_name = event_data.get("client_name")
            payment_id = event_data.get("payment_id")
            status = event_data.get("status")

            # 1. In-app notification for client
            create_in_app_notification.delay(
                user_id=str(user_id),
                title="Payment Proof Submitted",
                message=f"Your payment proof for Order #{order_number} has been received and is pending verification.",
                notification_type="info",
                action_url=f"/client/orders/{order_number}"
            )

            # 2. In-app notification for admin room (broadcast)
            create_in_app_notification.delay(
                user_id="__admin_broadcast__",
                title="Action Required: Verify Payment",
                message=f"Client {client_name} submitted payment proof for Order #{order_number}.",
                notification_type="warning",
                action_url=f"/admin/orders/{order_number}"
            )

            # 3. SocketIO emits
            room = f"user_{user_id}"
            socketio.emit("dashboard:payment_updated", {
                "payment_id": str(payment_id),
                "status": status
            }, to=room)
            
            socketio.emit("admin:payment_verification_required", {
                "payment_id": str(payment_id),
                "order_number": order_number,
                "client_name": client_name
            }, to="admin_room")
            
        except Exception as exc:
            logger.error("[PaymentEventHandlers] Error in payment.client_marked_paid handler: %r", exc)
            logger.error("[PaymentEventHandlers] Error in payment.client_marked_paid handler: %r", exc)

    def _on_payment_verified_by_admin(self, event_data: Dict[str, Any]) -> None:
        try:
            logger.info("[PaymentEventHandlers] Processing payment.verified_by_admin: %s", event_data.get("payment_id"))
            from tuned.tasks.notifications import create_in_app_notification
            from tuned.extensions import socketio
            
            user_id = event_data.get("user_id")
            order_number = event_data.get("order_number")
            payment_id = event_data.get("payment_id")
            status = event_data.get("status")

            create_in_app_notification.delay(
                user_id=str(user_id),
                title="Payment Verified Successfully",
                message=f"Your payment for Order #{order_number} has been verified. The order is now active!",
                notification_type="success",
                action_url=f"/client/orders/{order_number}"
            )

            # Direct referral reward trigger from payment verification
            try:
                from tuned.tasks.referral_tasks import process_referral_reward_task
                process_referral_reward_task.delay(
                    str(payment_id),
                    str(user_id),
                )
            except Exception as exc:
                logger.error("[PaymentEventHandlers] Referral task dispatch failed: %r", exc)
            
            room = f"user_{user_id}"
            socketio.emit("dashboard:payment_verified", {
                "payment_id": str(payment_id),
                "status": status
            }, to=room)
            socketio.emit("dashboard:payment_updated", {
                "payment_id": str(payment_id),
                "status": status
            }, to=room)
            
        except Exception as exc:
            logger.error("[PaymentEventHandlers] Error in payment.verified_by_admin handler: %r", exc)
            logger.error("[PaymentEventHandlers] Error in payment.verified_by_admin handler: %r", exc)

    def _on_invoice_created(self, event_data: Dict[str, Any]) -> None:
        try:
            logger.info("[PaymentEventHandlers] Processing invoice.created: %s", event_data.get("invoice_id"))
            from tuned.tasks.notifications import create_in_app_notification
            
            user_id = event_data.get("user_id")
            invoice_id = event_data.get("invoice_id")
            invoice_number = event_data.get("invoice_number")
            order_number = event_data.get("order_number")

            create_in_app_notification.delay(
                user_id=str(user_id),
                title="Invoice Issued",
                message=f"An official invoice {invoice_number} has been generated for Order #{order_number}.",
                notification_type="info",
                action_url=f"/client/invoices/{invoice_id}"
            )
            
        except Exception as exc:
            logger.error("[PaymentEventHandlers] Error in invoice.created handler: %r", exc)
    
    def _on_marked_failed(self, event_data: Dict[str, Any]) -> None:
        try:
            logger.info("[PaymentEventHandlers] Processing payment.marked_failed: %s", event_data.get("payment_id"))
            from tuned.tasks.notifications import create_in_app_notification
            from tuned.extensions import socketio

            user_id = event_data.get("user_id")
            payment_id = event_data.get("payment_id")
            order_number = event_data.get("order_number")
            status = event_data.get("status")
            
            create_in_app_notification.delay(
                user_id=str(user_id),
                title="Payment Rejected",
                message=f"Payment for Order #{order_number} has been rejected. Please provide a valid payment proof.",
                notification_type="error",
                action_url=f"/client/orders/{order_number}"
            )
            
            room = f"user_{user_id}"
            socketio.emit("dashboard:payment_updated", {
                "payment_id": str(payment_id),
                "status": status
            }, to=room)
        except Exception as exc:
            logger.error("[PaymentEventHandlers] Error in payment.marked_failed handler: %r", exc)

    def _on_refund_processed(self, event_data: Dict[str, Any]) -> None:
        try:
            logger.info("[PaymentEventHandlers] Processing refund.processed: %s", event_data.get("refund_id"))
            from tuned.tasks.notifications import create_in_app_notification

            refund_id = event_data.get("refund_id")
            user_id = event_data.get("user_id")
            order_number = event_data.get("order_number")
            amount = event_data.get("amount")

            create_in_app_notification.delay(
                user_id=str(user_id),
                title="Refund Processed",
                message=f"A refund of {amount} has been processed for Order #{order_number}.",
                notification_type="info",
                action_url=f"/client/orders/{order_number}",
            )

            from tuned.extensions import socketio
            socketio.emit(
                "dashboard:refund_processed",
                {"refund_id": str(refund_id), "amount": str(amount)},
                to=f"user_{user_id}",
            )
        except Exception as exc:
            logger.error(f"[PaymentEventHandlers] Error in refund.processed handler: {exc!r}")
