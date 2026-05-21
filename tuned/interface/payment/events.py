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
        self.bus.on("payment.marked_failed", self._on_marked_failed)
        logger.info("[PaymentEventHandlers] registered")

    def _on_payment_created(self, event_data: Dict[str, Any]) -> None:
        try:
            logger.info(f"[PaymentEventHandlers] Processing payment.created: {event_data['payment_id']}")
            from tuned.extensions import socketio
            room = f"user_{event_data['user_id']}"
            socketio.emit("dashboard:payment_updated", {
                "payment_id": event_data["payment_id"],
                "status": event_data["status"]
            }, to=room)
        except Exception as exc:
            logger.error(f"[PaymentEventHandlers] Error in payment.created handler: {exc!r}")

    def _on_payment_client_marked_paid(self, event_data: Dict[str, Any]) -> None:
        try:
            logger.info(f"[PaymentEventHandlers] Processing payment.client_marked_paid: {event_data['payment_id']}")
            from tuned.utils.dependencies import get_services
            from tuned.services.email_service import send_payment_client_marked_paid, send_admin_payment_proof_submitted
            from tuned.tasks.notifications import create_in_app_notification
            from tuned.models import NotificationType
            from tuned.extensions import socketio

            services = get_services()
            payment = services._repos.payment.payment.get_by_id(event_data['payment_id'])
            order = services.order.get_by_id(str(payment.order_id))
            client = services._repos.user.get_user_by_id(str(payment.user_id))
            
            # 1. In-app notification for client
            create_in_app_notification.delay(
                user_id=str(client.id),
                title="Payment Proof Submitted",
                message=f"Your payment proof for Order #{order.order_number} has been received and is pending verification.",
                notification_type=NotificationType.INFO,
                action_url=f"/client/orders/{order.order_number}"
            )
            # 2. Email confirmation to the client
            send_payment_client_marked_paid(client, order, payment)
            
            # 3. Notify Admin
            admin = services._repos.user.get_admin_user()
            
            # In-app notification for admin
            create_in_app_notification.delay(
                user_id=str(admin.id),
                title="Action Required: Verify Payment",
                message=f"Client {client.get_name()} submitted payment proof for Order #{order.order_number}.",
                notification_type=NotificationType.WARNING,
                action_url=f"/admin/orders/{order.order_number}"
            )
            send_admin_payment_proof_submitted(admin, payment, client.get_name(), order.order_number)

            # 4. SocketIO emits
            room = f"user_{event_data['user_id']}"
            socketio.emit("dashboard:payment_updated", {
                "payment_id": event_data["payment_id"],
                "status": event_data["status"]
            }, to=room)
            
            socketio.emit("admin:payment_verification_required", {
                "payment_id": event_data["payment_id"],
                "order_number": order.order_number,
                "client_name": client.get_name()
            }, to=f"user_{admin.id}")
            
        except Exception as exc:
            logger.error(f"[PaymentEventHandlers] Error in payment.client_marked_paid handler: {exc!r}")

    def _on_payment_verified_by_admin(self, event_data: Dict[str, Any]) -> None:
        try:
            logger.info(f"[PaymentEventHandlers] Processing payment.verified_by_admin: {event_data['payment_id']}")
            from tuned.utils.dependencies import get_services
            from tuned.tasks.notifications import create_in_app_notification
            from tuned.services.email_service import send_client_payment_verification_success_email
            from tuned.models import NotificationType
            from tuned.extensions import socketio
            
            services = get_services()
            payment = services._repos.payment.payment.get_by_id(event_data['payment_id'])
            order = services._repos.order.get_by_id(str(payment.order_id))
            client = services._repos.user.get_user_by_id(str(payment.user_id))
            
            create_in_app_notification.delay(
                user_id=str(client.id),
                title="Payment Verified Successfully",
                message=f"Your payment for Order #{order.order_number} has been verified. The order is now active!",
                notification_type=NotificationType.SUCCESS,
                action_url=f"/client/orders/{order.order_number}"
            )
            
            send_client_payment_verification_success_email(user=client, payment=payment, order=order)

            room = f"user_{event_data['user_id']}"
            socketio.emit("dashboard:payment_verified", {
                "payment_id": event_data["payment_id"],
                "status": event_data["status"]
            }, to=room)
            socketio.emit("dashboard:payment_updated", {
                "payment_id": event_data["payment_id"],
                "status": event_data["status"]
            }, to=room)
            
        except Exception as exc:
            logger.error(f"[PaymentEventHandlers] Error in payment.verified_by_admin handler: {exc!r}")

    def _on_invoice_created(self, event_data: Dict[str, Any]) -> None:
        try:
            logger.info(f"[PaymentEventHandlers] Processing invoice.created: {event_data['invoice_id']}")
            from tuned.utils.dependencies import get_services
            from tuned.tasks.notifications import create_in_app_notification
            from tuned.services.email_service import send_invoice_created_email
            from tuned.models import NotificationType
            
            services = get_services()
            invoice = services.payment.invoice.get_details(event_data['invoice_id'])
            client = services._repos.user.get_user_by_id(event_data['user_id'])
            order = services._repos.order.get_by_id(invoice.order_id)
            
            create_in_app_notification.delay(
                user_id=str(client.id),
                title="Invoice Issued",
                message=f"An official invoice {invoice.invoice_number} has been generated for Order #{order.order_number}.",
                notification_type=NotificationType.INFO,
                action_url=f"/client/invoices/{invoice.id}"
            )
            
            send_invoice_created_email(client, invoice, order.order_number)
            
        except Exception as exc:
            logger.error(f"[PaymentEventHandlers] Error in invoice.created handler: {exc!r}")

    def _on_marked_failed(self, event_data: Dict[str, Any]) -> None:
        try:
            logger.info(f"[PaymentEventHandlers] Processing payment.marked_failed: {event_data['payment_id']}")
            from tuned.utils.dependencies import get_services
            from tuned.tasks.notifications import create_in_app_notification
            from tuned.services.email_service import send_client_payment_verification_failure_email
            from tuned.models import NotificationType
            from tuned.extensions import socketio

            services = get_services()
            payment = services._repos.payment.payment.get_by_id(event_data['payment_id'])
            order = services._repos.order.get_by_id(str(payment.order_id))
            client = services._repos.user.get_user_by_id(str(payment.user_id))
            
            create_in_app_notification.delay(
                user_id=str(client.id),
                title="Payment Rejected",
                message=f"Payment for Order #{order.order_number} has been rejected. Please provide a valid payment proof.",
                notification_type=NotificationType.ERROR,
                action_url=f"/client/orders/{order.order_number}"
            )
            send_client_payment_verification_failure_email(client, order.order_number, event_data['rejection_reason'])
            
            room = f"user_{payment.user_id}"
            socketio.emit("dashboard:payment_updated", {
                "payment_id": str(payment.id),
                "status": payment.status.value
            }, to=room)
        except Exception as exc:
            logger.error(f"[PaymentEventHandlers] Error in payment.marked_failed handler: {exc!r}")

    def _on_refund_processed(self, event_data: Dict[str, Any]) -> None:
        try:
            logger.info(
                f"[PaymentEventHandlers] Processing refund.processed: {event_data['refund_id']}"
            )
            from tuned.utils.dependencies import get_services
            from tuned.tasks.notifications import create_in_app_notification
            from tuned.services.email_service import send_refund_processed_email
            from tuned.models import NotificationType

            services = get_services()
            refund = services._repos.payment.refund.get_by_id(event_data["refund_id"])
            payment = services._repos.payment.payment.get_by_id(str(refund.payment_id))
            order = services._repos.order.get_by_id(str(payment.order_id))
            client = services._repos.user.get_user_by_id(str(payment.user_id))

            create_in_app_notification.delay(
                user_id=str(client.id),
                title="Refund Processed",
                message=(
                    f"A refund of {refund.amount} has been processed for "
                    f"Order #{order.order_number}."
                ),
                notification_type=NotificationType.INFO,
                action_url=f"/client/orders/{order.order_number}",
            )

            send_refund_processed_email(client, order, refund)

            from tuned.extensions import socketio
            socketio.emit(
                "dashboard:refund_processed",
                {"refund_id": str(refund.id), "amount": str(refund.amount)},
                to=f"user_{client.id}",
            )
        except Exception as exc:
            logger.error(
                f"[PaymentEventHandlers] Error in refund.processed handler: {exc!r}"
            )
