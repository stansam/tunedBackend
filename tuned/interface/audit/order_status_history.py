from __future__ import annotations
import logging
from typing import List, Any, Optional, TYPE_CHECKING
from tuned.dtos import OrderStatusHistoryCreateDTO, OrderStatusHistoryResponseDTO, AuditListResponseDTO
from tuned.repository.exceptions import DatabaseError, NotFound
from tuned.core.logging import get_logger

if TYPE_CHECKING:
    from tuned.repository import Repository
    from tuned.repository.protocols.audit import OrderStatusHistoryRepositoryProtocol

logger: logging.Logger = get_logger(__name__)

class OrderStatusHistoryService:
    def __init__(self, repos: Optional[Repository] = None) -> None:
        self._repo: OrderStatusHistoryRepositoryProtocol
        if repos:
            self._repo = repos.audit.order_status_history
        else:
            from tuned.repository import repositories
            self._repo = repositories.audit.order_status_history

    def log_status_change(self, data: OrderStatusHistoryCreateDTO) -> OrderStatusHistoryResponseDTO:
        try:
            logger.info("Logging order status history: order=%s status=%s", data.order_id, data.new_status)
            return self._repo.create(data)
        except DatabaseError as e:
            logger.error("Database error while logging order status history: %s", str(e))
            raise

    def get_history_record(self, history_id: str) -> OrderStatusHistoryResponseDTO:
        try:
            return self._repo.get_by_id(history_id)
        except NotFound:
            logger.error("Order status history record not found: %s", history_id)
            raise
        except DatabaseError as e:
            logger.error("Database error while fetching order status history: %s", str(e))
            raise

    def get_order_history(self, order_id: str, page: int = 1, per_page: int = 20) -> AuditListResponseDTO[OrderStatusHistoryResponseDTO]:
        try:
            items, total = self._repo.get_by_order(order_id, page, per_page)
            return AuditListResponseDTO[OrderStatusHistoryResponseDTO](
                items=list(items),
                total=total,
                page=page,
                per_page=per_page
            )
        except DatabaseError as e:
            logger.error("Database error while fetching order history: %s", str(e))
            raise
