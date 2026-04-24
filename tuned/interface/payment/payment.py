from __future__ import annotations
import logging
from tuned.core.logging import get_logger
from tuned.dtos.audit import ActivityLogCreateDTO
from tuned.dtos.payment import PaymentCreateDTO, PaymentUpdateDTO, PaymentResponseDTO
from tuned.interface.audit import audit_service
from tuned.repository import repositories
from tuned.utils.variables import Variables
from tuned.core.events import get_event_bus

logger: logging.Logger = get_logger(__name__)

class ProcessPayment:
    def __init__(self) -> None:
        self._repo = repositories.payment.payment
        self._audit = audit_service
    def execute(self, data: PaymentCreateDTO) -> PaymentResponseDTO:
        try:
            payment = self._repo.create(data)
            
            try:
                self._audit.activity_log.log(ActivityLogCreateDTO(
                    action=Variables.PAYMENT_CREATE_ACTION,
                    user_id=data.user_id,
                    entity_type=Variables.PAYMENT_ENTITY_TYPE,
                    entity_id=payment.id,
                    after={"amount": data.amount, "status": payment.status, "method": payment.method},
                    created_by=data.user_id,
                ))
            except Exception as audit_exc:
                logger.error(f"[ProcessPayment] Audit failed for payment {payment.id}: {audit_exc!r}")

            try:
                get_event_bus().emit("payment.created", {
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
    def __init__(self) -> None:
        self._repo = repositories.payment.payment
    def execute(self, payment_id: str) -> PaymentResponseDTO:
        try:
            return self._repo.get_by_id(payment_id)
        except Exception as exc:
            logger.error(f"[GetPaymentDetails] Failed to get payment {payment_id}: {exc!r}")
            raise

class UpdatePaymentStatus:
    def __init__(self) -> None:
        self._repo = repositories.payment.payment
        self._audit = audit_service
    def execute(self, payment_id: str, data: PaymentUpdateDTO, actor_id: str) -> PaymentResponseDTO:
        try:
            payment = self._repo.update(payment_id, data)

            try:
                self._audit.activity_log.log(ActivityLogCreateDTO(
                    action=Variables.PAYMENT_UPDATE_ACTION,
                    user_id=payment.user_id,
                    entity_type=Variables.PAYMENT_ENTITY_TYPE,
                    entity_id=payment.id,
                    after={"status": payment.status},
                    created_by=actor_id,
                ))
            except Exception as audit_exc:
                logger.error(f"[UpdatePaymentStatus] Audit failed for payment {payment.id}: {audit_exc!r}")

            try:
                get_event_bus().emit("payment.updated", {
                    "payment_id": payment.id,
                    "order_id": payment.order_id,
                    "user_id": payment.user_id,
                    "status": payment.status
                })
            except Exception as event_exc:
                logger.error(f"[UpdatePaymentStatus] Event emit failed for payment {payment.id}: {event_exc!r}")

            logger.info(f"[UpdatePaymentStatus] Payment {payment.id} status updated to {payment.status}")
            return payment
        except Exception as exc:
            logger.error(f"[UpdatePaymentStatus] Failed to update payment {payment_id}: {exc!r}")
            raise
