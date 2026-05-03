from __future__ import annotations
import logging
from typing import Optional, TYPE_CHECKING
from tuned.core.logging import get_logger
from tuned.dtos.audit import ActivityLogCreateDTO
from tuned.dtos.payment import TransactionCreateDTO, TransactionResponseDTO
from tuned.utils.variables import Variables

if TYPE_CHECKING:
    from tuned.repository import Repository

logger: logging.Logger = get_logger(__name__)

class LogTransaction:
    def __init__(self, repos: Repository) -> None:
        self._repo = repos.payment.transaction
        from tuned.interface.audit import AuditService
        self._audit = AuditService(repos=repos)

    def execute(self, data: TransactionCreateDTO, actor_id: str) -> TransactionResponseDTO:
        try:
            transaction = self._repo.create(data)

            try:
                self._audit.activity_log.log(ActivityLogCreateDTO(
                    action=Variables.TRANSACTION_CREATE_ACTION,
                    user_id=actor_id,
                    entity_type=Variables.TRANSACTION_ENTITY_TYPE,
                    entity_id=transaction.id,
                    after={"amount": transaction.amount, "type": transaction.type, "status": transaction.status},
                    created_by=actor_id,
                    ip_address="system",
                    user_agent="system"
                ))
                logger.info(f"[LogTransaction] Audit successfully applied for transaction {transaction.transaction_id}")
            except Exception as audit_exc:
                logger.error(f"[LogTransaction] Audit failed for transaction {transaction.id}: {audit_exc!r}")

            logger.info(f"[LogTransaction] Transaction {transaction.transaction_id} logged for payment {transaction.payment_id}")
            return transaction
        except Exception as exc:
            logger.error(f"[LogTransaction] Failed to log transaction: {exc!r}")
            raise

class GetTransactionHistory:
    def __init__(self, repos: Repository) -> None:
        self._repo = repos.payment.transaction

    def execute(self, payment_id: str) -> list[TransactionResponseDTO]:
        try:
            return self._repo.get_by_payment_id(payment_id)
        except Exception as exc:
            logger.error(f"[GetTransactionHistory] Failed to fetch transaction history for payment {payment_id}: {exc!r}")
            raise
