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
            payment = self._repo.get_by_id(payment_id)
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
                    payment_id=updated_payment.id,
                    type=TransactionType.PAYMENT,
                    amount=updated_payment.amount,
                    status=TransactionStatus.PENDING
                ))
            except Exception as tx_exc:
                logger.error(f"[ClientMarkAsPaid] Transaction record creation failed for payment {updated_payment.id}: {tx_exc!r}")

            try:
                self._audit.activity_log.log(ActivityLogCreateDTO(
                    action=Variables.PAYMENT_UPDATE_ACTION,
                    user_id=updated_payment.user_id,
                    entity_type=Variables.PAYMENT_ENTITY_TYPE,
                    entity_id=updated_payment.id,
                    before=payment,
                    after=updated_payment,
                    created_by=client_id,
                    ip_address="system",
                    user_agent="system"
                ))
            except Exception as audit_exc:
                logger.error(f"[ClientMarkAsPaid] Audit failed for payment {updated_payment.id}: {audit_exc!r}")
            self._repos.payment.save()

            try:
                event_bus.emit("payment.client_marked_paid", {
                    "payment_id": updated_payment.id,
                    "order_id": updated_payment.order_id,
                    "user_id": updated_payment.user_id,
                    "status": updated_payment.status
                })
            except Exception as event_exc:
                logger.error(f"[ClientMarkAsPaid] Event emit failed for payment {updated_payment.id}: {event_exc!r}")

            logger.info(f"[ClientMarkAsPaid] Payment {updated_payment.id} marked as paid by client {client_id}")
            return updated_payment
        except Exception as exc:
            logger.error(f"[ClientMarkAsPaid] Failed to mark payment {payment_id} as paid: {exc!r}")
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
                    payment_id=updated_payment.id,
                    type=TransactionType.PAYMENT,
                    amount=updated_payment.amount,
                    status=TransactionStatus.COMPLETED
                ))
            except Exception as tx_exc:
                logger.error(f"[AdminVerifyPayment] Transaction record creation failed for payment {updated_payment.id}: {tx_exc!r}")

            order = self._repos.order.get_by_id(updated_payment.order_id)
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
                    payment_id=updated_payment.id,
                    discount=float(order.discount_amount or 0.0),
                    tax=0.0,
                    paid=True
                )
                self._repos.payment.invoice.create(invoice_dto)
                

            try:
                self._audit.activity_log.log(ActivityLogCreateDTO(
                    action=Variables.PAYMENT_UPDATE_ACTION,
                    user_id=updated_payment.user_id,
                    entity_type=Variables.PAYMENT_ENTITY_TYPE,
                    entity_id=updated_payment.id,
                    before=payment,
                    after=updated_payment,
                    created_by=admin_id,
                    ip_address="system",
                    user_agent="system"
                ))
            except Exception as audit_exc:
                logger.error(f"[AdminVerifyPayment] Audit failed for payment {updated_payment.id}: {audit_exc!r}")
            self._repos.payment.save()
            try:
                event_bus.emit("payment.verified_by_admin", {
                    "payment_id": updated_payment.id,
                    "order_id": updated_payment.order_id,
                    "user_id": updated_payment.user_id,
                    "status": updated_payment.status
                })
            except Exception as event_exc:
                logger.error(f"[AdminVerifyPayment] Event emit failed for payment {updated_payment.id}: {event_exc!r}")

            logger.info(f"[AdminVerifyPayment] Payment {updated_payment.id} verified by admin {admin_id}")
            return updated_payment
        except Exception as exc:
            logger.error(f"[AdminVerifyPayment] Failed to verify payment {payment_id}: {exc!r}")
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
                    payment_id=updated_payment.id,
                    type=TransactionType.PAYMENT,
                    amount=updated_payment.amount,
                    status=TransactionStatus.FAILED
                ))
            except Exception as tx_exc:
                logger.error(f"[AdminRejectPayment] Transaction record creation failed for payment {updated_payment.id}: {tx_exc!r}")

            try:
                self._audit.activity_log.log(ActivityLogCreateDTO(
                    action=Variables.PAYMENT_UPDATE_ACTION,
                    user_id=updated_payment.user_id,
                    entity_type=Variables.PAYMENT_ENTITY_TYPE,
                    entity_id=updated_payment.id,
                    before=payment,
                    after=updated_payment,
                    created_by=user_id,
                    ip_address=ip_address,
                    user_agent=user_agent
                ))
            except Exception as audit_exc:
                logger.error(f"[AdminRejectPayment] Audit failed for payment {updated_payment.id}: {audit_exc!r}")
            self._repos.payment.save()
            try:
                event_bus.emit("payment.marked_failed", {
                    "payment_id": updated_payment.id,
                    "rejection_reason": rejection_reason
                })
            except Exception as event_exc:
                logger.error(f"[AdminRejectPayment] Event emit failed for payment {updated_payment.id}: {event_exc!r}")

            logger.info(f"[AdminRejectPayment] Payment {updated_payment.id} rejected by admin {user_id}")
            return updated_payment
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