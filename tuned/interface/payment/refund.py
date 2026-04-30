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
    def __init__(self, repos: Optional[Repository] = None) -> None:
        if repos:
            self._repo = repos.payment.refund
            from tuned.interface.audit import AuditService
            self._audit = AuditService(repos=repos)
        else:
            from tuned.repository import repositories
            self._repo = repositories.payment.refund
            from tuned.interface.audit import audit_service
            self._audit = audit_service

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
    def __init__(self, repos: Optional[Repository] = None) -> None:
        if repos:
            self._repo = repos.payment.refund
            from tuned.interface.audit import AuditService
            self._audit = AuditService(repos=repos)
        else:
            from tuned.repository import repositories
            self._repo = repositories.payment.refund
            from tuned.interface.audit import audit_service
            self._audit = audit_service

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
                logger.error(f"[ApproveRefund] Audit failed for refund {refund.id}: {audit_exc!r}")

            try:
                event_bus.emit("refund.processed", {
                    "refund_id": refund.id,
                    "payment_id": refund.payment_id,
                    "status": refund.status
                })
            except Exception as event_exc:
                logger.error(f"[ApproveRefund] Event emit failed for refund {refund.id}: {event_exc!r}")

            logger.info(f"[ApproveRefund] Refund {refund.id} approved by admin {admin_id}")
            return refund
        except Exception as exc:
            logger.error(f"[ApproveRefund] Failed to approve refund {refund_id}: {exc!r}")
            raise
