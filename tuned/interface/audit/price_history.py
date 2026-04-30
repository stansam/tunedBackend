from __future__ import annotations
import logging
from typing import List, Any, Optional, TYPE_CHECKING
from tuned.dtos import PriceHistoryCreateDTO, PriceHistoryResponseDTO, AuditListResponseDTO
from tuned.repository.exceptions import DatabaseError, NotFound
from tuned.core.logging import get_logger

if TYPE_CHECKING:
    from tuned.repository import Repository
    from tuned.repository.protocols.audit import PriceHistoryRepositoryProtocol

logger: logging.Logger = get_logger(__name__)

class PriceHistoryService:
    def __init__(self, repos: Optional[Repository] = None) -> None:
        self._repo: PriceHistoryRepositoryProtocol
        if repos:
            self._repo = repos.audit.price_history
        else:
            from tuned.repository import repositories
            self._repo = repositories.audit.price_history

    def log_price_change(self, data: PriceHistoryCreateDTO) -> PriceHistoryResponseDTO:
        try:
            logger.info("Logging price history: rate=%s new_price=%s", data.price_rate_id, data.new_price)
            return self._repo.create(data)
        except DatabaseError as e:
            logger.error("Database error while logging price history: %s", str(e))
            raise

    def get_history_record(self, history_id: str) -> PriceHistoryResponseDTO:
        try:
            return self._repo.get_by_id(history_id)
        except NotFound:
            logger.error("Price history record not found: %s", history_id)
            raise
        except DatabaseError as e:
            logger.error("Database error while fetching price history: %s", str(e))
            raise

    def get_rate_history(self, rate_id: str, page: int = 1, per_page: int = 20) -> AuditListResponseDTO[PriceHistoryResponseDTO]:
        try:
            items, total = self._repo.get_by_rate(rate_id, page, per_page)
            return AuditListResponseDTO[PriceHistoryResponseDTO](
                items=list(items),
                total=total,
                page=page,
                per_page=per_page
            )
        except DatabaseError as e:
            logger.error("Database error while fetching rate history: %s", str(e))
            raise
