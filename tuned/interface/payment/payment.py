from __future__ import annotations
import logging
from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
from tuned.core.logging import get_logger
from tuned.dtos import ActivityLogCreateDTO, PaymentCreateDTO, PaymentUpdateDTO, PaymentResponseDTO
from tuned.utils.variables import Variables
from tuned.core.events import get_event_bus
from tuned.models import PaymentStatus

if TYPE_CHECKING:
    from tuned.repository import Repository

logger: logging.Logger = get_logger(__name__)
event_bus = get_event_bus()

class ProcessPayment:
    def __init__(self, repos: Repository) -> None:
        self._repo = repos.payment.payment
        from tuned.interface.audit import AuditService
        self._audit = AuditService(repos=repos)

    def execute(self, data: PaymentCreateDTO) -> PaymentResponseDTO:
        try:
            payment = self._repo.create(data)
            
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
            return self._repo.get_by_id(payment_id)
        except Exception as exc:
            logger.error(f"[GetPaymentDetails] Failed to get payment {payment_id}: {exc!r}")
            raise

class ClientMarkAsPaid:
    def __init__(self, repos: Repository) -> None:
        self._repo = repos.payment.payment
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
        from tuned.interface.audit import AuditService
        self._audit = AuditService(repos=repos)
        
    def execute(self, payment_id: str, admin_id: str) -> PaymentResponseDTO:
        try:
            from tuned.models import PaymentStatus
            from datetime import datetime, timezone
            
            payment = self._repo.get_by_id(payment_id)
            if payment.status != PaymentStatus.PENDING_VERIFICATION.value and payment.status != PaymentStatus.PENDING_VERIFICATION:
                raise ValueError(f"Payment is not awaiting verification, current state: {payment.status}")
                
            data = PaymentUpdateDTO(
                status=PaymentStatus.COMPLETED,
                admin_verified_at=datetime.now(timezone.utc)
            )
            updated_payment = self._repo.update(payment_id, data)

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
