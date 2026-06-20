from __future__ import annotations
import logging
from typing import Optional, TYPE_CHECKING
from tuned.core.logging import get_logger
from tuned.models.enums import RefundStatus
from tuned.dtos.audit import ActivityLogCreateDTO
from tuned.dtos.payment import RefundCreateDTO, RefundUpdateDTO, RefundResponseDTO
from tuned.utils.variables import Variables
from tuned.core.events import get_event_bus

if TYPE_CHECKING:
    from tuned.repository import Repository

logger: logging.Logger = get_logger(__name__)
event_bus = get_event_bus()

class ProcessRefund:
    def __init__(self, repos: Repository) -> None:
        self._repo = repos.payment.refund
        from tuned.interface.audit import AuditService
        self._audit = AuditService(repos=repos)

    def execute(self, data: RefundCreateDTO) -> RefundResponseDTO:
        try:
            refund = self._repo.create(data)

            try:
                self._audit.activity_log.log(ActivityLogCreateDTO(
                    action=Variables.REFUND_CREATE_ACTION,
                    user_id=data.processed_by, # Admin or system
                    entity_type=Variables.REFUND_ENTITY_TYPE,
                    entity_id=refund.id,
                    after=refund,
                    created_by=data.processed_by,
                    ip_address="system",
                    user_agent="system"
                ))
            except Exception as audit_exc:
                logger.error(f"[ProcessRefund] Audit failed for refund {refund.id}: {audit_exc!r}")

            try:
                event_bus.emit("refund.created", {
                    "refund_id": refund.id,
                    "payment_id": refund.payment_id,
                    "amount": refund.amount,
                    "status": refund.status
                })
            except Exception as event_exc:
                logger.error(f"[ProcessRefund] Event emit failed for refund {refund.id}: {event_exc!r}")

            logger.info(f"[ProcessRefund] Refund {refund.id} processed by {data.processed_by}")
            return refund
        except Exception as exc:
            logger.error(f"[ProcessRefund] Failed to process refund: {exc!r}")
            raise

class ApproveRefund:
    def __init__(self, repos: Repository) -> None:
        self._repo = repos.payment.refund
        self._repos = repos
        from tuned.interface.audit import AuditService
        self._audit = AuditService(repos=repos)

    def execute(self, refund_id: str, admin_id: str) -> RefundResponseDTO:
        try:
            data = RefundUpdateDTO(status=RefundStatus.PROCESSED)
            refund = self._repo.update_status(refund_id, data)

            try:
                self._audit.activity_log.log(ActivityLogCreateDTO(
                    action=Variables.REFUND_UPDATE_ACTION,
                    user_id=admin_id,
                    entity_type=Variables.REFUND_ENTITY_TYPE,
                    entity_id=refund.id,
                    after=refund,
                    created_by=admin_id,
                    ip_address="system",
                    user_agent="system"
                ))
            except Exception as audit_exc:
                logger.error("[ApproveRefund] Audit failed for refund %s: %r", refund.id, audit_exc)

            try:
                payment = self._repos.payment.payment.get_by_id(str(refund.payment_id))
                order = self._repos.order.get_by_id(str(payment.order_id))
                client = self._repos.user.get_user_by_id(str(payment.user_id))

                # Email notification
                try:
                    from tuned.services.email_service import send_refund_processed_email
                    send_refund_processed_email(client, order, refund)
                except Exception as email_exc:
                    logger.error("[ApproveRefund] Email confirmation failed: %r", email_exc)

                event_bus.emit("refund.processed", {
                    "refund_id":    str(refund.id),
                    "payment_id":   str(refund.payment_id),
                    "order_id":     str(payment.order_id),
                    "order_number": order.order_number,
                    "user_id":      str(payment.user_id),
                    "client_name":  client.get_name(),
                    "client_email": client.email,
                    "amount":       float(refund.amount),
                    "reason":       refund.reason,
                })
            except Exception as event_exc:
                logger.error("[ApproveRefund] Event emit failed for refund %s: %r", refund.id, event_exc)

            logger.info("[ApproveRefund] Refund %s approved by admin %s", refund.id, admin_id)
            return refund
        except Exception as exc:
            logger.error(f"[ApproveRefund] Failed to approve refund {refund_id}: {exc!r}")
            raise
