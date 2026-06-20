from __future__ import annotations
import logging
from sqlalchemy import select
from datetime import datetime, timezone, timedelta
from typing import Optional, TYPE_CHECKING
from tuned.core.logging import get_logger
from tuned.dtos import ActivityLogCreateDTO, PaymentCreateDTO, PaymentUpdateDTO, PaymentResponseDTO, InvoiceCreateDTO, TransactionCreateDTO
from tuned.utils.variables import Variables
from tuned.core.events import get_event_bus
from tuned.models import PaymentStatus, OrderStatus, Order, TransactionType, TransactionStatus

if TYPE_CHECKING:
    from tuned.repository import Repository

logger: logging.Logger = get_logger(__name__)
event_bus = get_event_bus()

class ProcessPayment:
    def __init__(self, repos: Repository) -> None:
        self._repo = repos.payment.payment
        self._repos = repos
        from tuned.interface.audit import AuditService
        self._audit = AuditService(repos=repos)

    def execute(self, data: PaymentCreateDTO) -> PaymentResponseDTO:
        try:
            payment = self._repo.create(data)
            
            try:
                self._repos.payment.transaction.create(TransactionCreateDTO(
                    payment_id=payment.id,
                    type=TransactionType.PAYMENT,
                    amount=payment.amount,
                    status=TransactionStatus.PENDING
                ))
            except Exception as tx_exc:
                logger.error(f"[ProcessPayment] Transaction record creation failed for payment {payment.id}: {tx_exc!r}")

            try:
                self._audit.activity_log.log(ActivityLogCreateDTO(
                    action=Variables.PAYMENT_CREATE_ACTION,
                    user_id=data.user_id,
                    entity_type=Variables.PAYMENT_ENTITY_TYPE,
                    entity_id=payment.id,
                    after=payment,
                    created_by=data.user_id,
                    ip_address="system",
                    user_agent="system"
                ))
            except Exception as audit_exc:
                logger.error(f"[ProcessPayment] Audit failed for payment {payment.id}: {audit_exc!r}")
            self._repos.payment.save()
            try:
                event_bus.emit("payment.created", {
                    "payment_id": payment.id,
                    "order_id": payment.order_id,
                    "user_id": payment.user_id,
                    "amount": payment.amount,
                    "status": payment.status
                })
            except Exception as event_exc:
                logger.error(f"[ProcessPayment] Event emit failed for payment {payment.id}: {event_exc!r}")

            logger.info(f"[ProcessPayment] User {data.user_id} created payment {payment.id}")
            return payment
        except Exception as exc:
            logger.error(f"[ProcessPayment] Failed to process payment: {exc!r}")
            raise

class GetPaymentDetails:
    def __init__(self, repos: Repository) -> None:
        self._repo = repos.payment.payment

    def execute(self, payment_id: str) -> PaymentResponseDTO:
        try:
            payment = self._repo.get_by_id(payment_id)
            return PaymentResponseDTO.from_model(payment)
        except Exception as exc:
            logger.error(f"[GetPaymentDetails] Failed to get payment {payment_id}: {exc!r}")
            raise

class ClientMarkAsPaid:
    def __init__(self, repos: Repository) -> None:
        self._repo = repos.payment.payment
        self._repos = repos 
        from tuned.interface.audit import AuditService
        self._audit = AuditService(repos=repos)
        
    def execute(self, payment_id: str, client_proof_reference: str, client_id: str) -> PaymentResponseDTO:
        try:
            client = self._repos.user.get_user_by_id(client_id)
            payment = self._repo.get_by_id(payment_id)
            order = self._repos.order.get_by_id(str(payment.order_id))
            if payment.status != PaymentStatus.PENDING:
                raise ValueError(f"Payment is not in a pending state, current state: {payment.status}")
                
            data = PaymentUpdateDTO(
                status=PaymentStatus.PENDING_VERIFICATION,
                client_proof_reference=client_proof_reference,
                client_marked_paid_at=datetime.now(timezone.utc)
            )
            updated_payment = self._repo.update(payment_id, data)

            try:
                self._repos.payment.transaction.create(TransactionCreateDTO(
                    payment_id=str(updated_payment.id),
                    type=TransactionType.PAYMENT,
                    amount=updated_payment.amount,
                    status=TransactionStatus.PENDING
                ))
            except Exception as tx_exc:
                logger.error(f"[ClientMarkAsPaid] Transaction record creation failed for payment {updated_payment.id}: {tx_exc!r}")

            try:
                self._audit.activity_log.log(ActivityLogCreateDTO(
                    action=Variables.PAYMENT_UPDATE_ACTION,
                    user_id=str(updated_payment.user_id),
                    entity_type=Variables.PAYMENT_ENTITY_TYPE,
                    entity_id=str(updated_payment.id),
                    before=payment,
                    after=updated_payment,
                    created_by=client_id,
                    ip_address="system",
                    user_agent="system"
                ))
            except Exception as audit_exc:
                logger.error(f"[ClientMarkAsPaid] Audit failed for payment {updated_payment.id}: {audit_exc!r}")
            self._repos.payment.save()

            # 2. Email confirmation to the client and admin
            try:
                from tuned.services.email_service import send_payment_client_marked_paid, send_admin_payment_proof_submitted
                send_payment_client_marked_paid(client, order, updated_payment)
                admin = self._repos.user.get_admin_user()
                send_admin_payment_proof_submitted(admin, updated_payment, client.get_name(), order.order_number)
            except Exception as email_exc:
                logger.error("[ClientMarkAsPaid] Email confirmation failed: %r", email_exc)

            try:
                event_bus.emit("payment.client_marked_paid", {
                    "payment_id":      str(updated_payment.id),
                    "order_id":        str(updated_payment.order_id),
                    "order_number":    order.order_number,
                    "user_id":         str(updated_payment.user_id),
                    "client_name":     client.get_name(),
                    "client_email":    client.email,
                    "status":          updated_payment.status.value,
                    "amount":          float(updated_payment.amount),
                })
            except Exception as event_exc:
                logger.error("[ClientMarkAsPaid] Event emit failed for payment %s: %r", updated_payment.id, event_exc)

            logger.info("[ClientMarkAsPaid] Payment %s marked as paid by client %s", updated_payment.id, client_id)
            return PaymentResponseDTO.from_model(updated_payment)
        except Exception as exc:
            logger.error("[ClientMarkAsPaid] Failed to mark payment %s as paid: %r", payment_id, exc)
            raise

class AdminVerifyPayment:
    def __init__(self, repos: Repository) -> None:
        self._repo = repos.payment.payment
        self._repos = repos
        from tuned.interface.audit import AuditService
        self._audit = AuditService(repos=repos)
        
    def execute(self, payment_id: str, admin_id: str) -> PaymentResponseDTO:
        try:
            payment = self._repo.get_by_id(payment_id)
            if payment.status != PaymentStatus.PENDING_VERIFICATION:
                raise ValueError(f"Payment is not awaiting verification, current state: {payment.status}")
                
            data = PaymentUpdateDTO(
                status=PaymentStatus.COMPLETED,
                admin_verified_at=datetime.now(timezone.utc)
            )
            updated_payment = self._repo.update(payment_id, data)

            try:
                self._repos.payment.transaction.create(TransactionCreateDTO(
                    payment_id=str(updated_payment.id),
                    type=TransactionType.PAYMENT,
                    amount=updated_payment.amount,
                    status=TransactionStatus.COMPLETED
                ))
            except Exception as tx_exc:
                logger.error("[AdminVerifyPayment] Transaction record creation failed for payment %s: %r", updated_payment.id, tx_exc)

            order = self._repos.order.get_by_id(str(updated_payment.order_id))
            # Update Order paid status and transition to ACTIVE
            if order:
                order.paid = True
                order.status = OrderStatus.ACTIVE
                
                # Auto-generate paid invoice
                invoice_dto = InvoiceCreateDTO(
                    order_id=str(order.id),
                    user_id=str(order.client_id),
                    subtotal=float(order.subtotal or order.total_price or 0.0),
                    total=float(order.total_price or 0.0),
                    due_date=datetime.now(timezone.utc) + timedelta(days=14),
                    payment_id=str(updated_payment.id),
                    discount=float(order.discount_amount or 0.0),
                    tax=0.0,
                    paid=True
                )
                self._repos.payment.invoice.create(invoice_dto)
                

            try:
                self._audit.activity_log.log(ActivityLogCreateDTO(
                    action=Variables.PAYMENT_UPDATE_ACTION,
                    user_id=str(updated_payment.user_id),
                    entity_type=Variables.PAYMENT_ENTITY_TYPE,
                    entity_id=str(updated_payment.id),
                    before=payment,
                    after=updated_payment,
                    created_by=admin_id,
                    ip_address="system",
                    user_agent="system"
                ))
            except Exception as audit_exc:
                logger.error("[AdminVerifyPayment] Audit failed for payment %s: %r", updated_payment.id, audit_exc)
            self._repos.payment.save()

            # Email notification
            try:
                from tuned.services.email_service import send_client_payment_verification_success_email
                client = self._repos.user.get_user_by_id(str(updated_payment.user_id))
                send_client_payment_verification_success_email(user=client, payment=updated_payment, order=order)
            except Exception as email_exc:
                logger.error("[AdminVerifyPayment] Email confirmation failed: %r", email_exc)

            try:
                order = self._repos.order.get_by_id(str(updated_payment.order_id))
                client = self._repos.user.get_user_by_id(str(updated_payment.user_id))
                event_bus.emit("payment.verified_by_admin", {
                    "payment_id":    str(updated_payment.id),
                    "order_id":      str(updated_payment.order_id),
                    "order_number":  order.order_number,
                    "user_id":       str(updated_payment.user_id),
                    "client_name":   client.get_name(),
                    "client_email":  client.email,
                    "status":        updated_payment.status.value,
                    "amount":        float(updated_payment.amount),
                })
            except Exception as event_exc:
                logger.error("[AdminVerifyPayment] Event emit failed for payment %s: %r", updated_payment.id, event_exc)

            logger.info("[AdminVerifyPayment] Payment %s verified by admin %s", updated_payment.id, admin_id)
            return PaymentResponseDTO.from_model(updated_payment)
        except Exception as exc:
            logger.error("[AdminVerifyPayment] Failed to verify payment %s: %r", payment_id, exc)
            raise

class AdminRejectPayment:
    def __init__(self, repos: Repository) -> None:
        self._repo = repos.payment.payment
        self._repos = repos
        from tuned.interface.audit import AuditService
        self._audit = AuditService(repos=repos)
        
    def execute(self, payment_id: str, user_id: str, rejection_reason: str = "Payment marked as failed by Admin", ip_address: str = "system", user_agent: str = "system") -> PaymentResponseDTO:
        try:
            payment = self._repo.get_by_id(payment_id)
            if payment.status != PaymentStatus.PENDING_VERIFICATION:
                raise ValueError(f"Payment is not awaiting verification, current state: {payment.status}")
                
            data = PaymentUpdateDTO(
                status=PaymentStatus.FAILED,
                admin_verified_at=datetime.now(timezone.utc)
            )
            updated_payment = self._repo.update(payment_id, data)

            try:
                self._repos.payment.transaction.create(TransactionCreateDTO(
                    payment_id=str(updated_payment.id),
                    type=TransactionType.PAYMENT,
                    amount=updated_payment.amount,
                    status=TransactionStatus.FAILED
                ))
            except Exception as tx_exc:
                logger.error("[AdminRejectPayment] Transaction record creation failed for payment %s: %r", updated_payment.id, tx_exc)

            try:
                self._audit.activity_log.log(ActivityLogCreateDTO(
                    action=Variables.PAYMENT_UPDATE_ACTION,
                    user_id=str(updated_payment.user_id),
                    entity_type=Variables.PAYMENT_ENTITY_TYPE,
                    entity_id=str(updated_payment.id),
                    before=payment,
                    after=updated_payment,
                    created_by=user_id,
                    ip_address=ip_address,
                    user_agent=user_agent
                ))
            except Exception as audit_exc:
                logger.error("[AdminRejectPayment] Audit failed for payment %s: %r", updated_payment.id, audit_exc)
            self._repos.payment.save()

            # Email notification
            try:
                from tuned.services.email_service import send_client_payment_verification_failure_email
                order = self._repos.order.get_by_id(str(updated_payment.order_id))
                client = self._repos.user.get_user_by_id(str(updated_payment.user_id))
                send_client_payment_verification_failure_email(client, order.order_number, rejection_reason)
            except Exception as email_exc:
                logger.error("[AdminRejectPayment] Email notification failed: %r", email_exc)

            try:
                order = self._repos.order.get_by_id(str(updated_payment.order_id))
                client = self._repos.user.get_user_by_id(str(updated_payment.user_id))
                event_bus.emit("payment.marked_failed", {
                    "payment_id":       str(updated_payment.id),
                    "order_id":         str(updated_payment.order_id),
                    "order_number":     order.order_number,
                    "user_id":          str(updated_payment.user_id),
                    "client_name":      client.get_name(),
                    "client_email":     client.email,
                    "status":           updated_payment.status.value,
                    "rejection_reason": rejection_reason,
                })
            except Exception as event_exc:
                logger.error("[AdminRejectPayment] Event emit failed for payment %s: %r", updated_payment.id, event_exc)

            logger.info("[AdminRejectPayment] Payment %s rejected by admin %s", updated_payment.id, user_id)
            return PaymentResponseDTO.from_model(updated_payment)
        except Exception as exc:
            logger.error(f"[AdminRejectPayment] Failed to reject payment {payment_id}: {exc!r}")
            raise


class ListPayments:
    def __init__(self, repos: Repository) -> None:
        self._repo = repos.payment.payment

    def execute(self, user_id: Optional[str] = None, status: Optional[str] = None, page: int = 1, per_page: int = 10) -> tuple[list[PaymentResponseDTO], int]:
        try:
            return self._repo.list_payments(user_id=user_id, status=status, page=page, per_page=per_page)
        except Exception as exc:
            logger.error(f"[ListPayments] Failed to list payments: {exc!r}")
            raise