from __future__ import annotations
import logging
from tuned.dtos import EmailLogCreateDTO, EmailLogResponseDTO, EmailLogUpdateDTO, EmailLogFilterDTO, AuditListResponseDTO
from tuned.repository.exceptions import DatabaseError, NotFound
from tuned.core.logging import get_logger
from typing import List, Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from tuned.repository import Repository
    from tuned.repository.protocols.audit import EmailLogRepositoryProtocol

logger: logging.Logger = get_logger(__name__)

class EmailLogService:
    def __init__(self, repos: Repository) -> None:
        self._repo = repos.audit.email_log

    def log(self, data: EmailLogCreateDTO) -> EmailLogResponseDTO:
        try:
            logger.info("Logging email: %s to %s", data.template, data.recipient)
            return self._repo.create(data)
        except DatabaseError as e:
            logger.error("Database error while logging email: %s", str(e))
            raise

    def get_log(self, log_id: str) -> EmailLogResponseDTO:
        try:
            return self._repo.get_by_id(log_id)
        except NotFound:
            logger.error("Email log record not found: %s", log_id)
            raise
        except DatabaseError as e:
            logger.error("Database error while fetching email log: %s", str(e))
            raise

    def update_status(self, log_id: str, data: EmailLogUpdateDTO) -> EmailLogResponseDTO:
        try:
            return self._repo.update_status(log_id, data)
        except NotFound:
            logger.error("Email log record not found: %s", log_id)
            raise
        except DatabaseError as e:
            logger.error("Database error while updating email log: %s", str(e))
            raise

    def query_logs(self, filters: EmailLogFilterDTO) -> AuditListResponseDTO[EmailLogResponseDTO]:
        try:
            items, total = self._repo.get_filtered(filters)
            return AuditListResponseDTO[EmailLogResponseDTO](
                items=list(items),
                total=total,
                page=filters.page,
                per_page=filters.per_page
            )
        except DatabaseError as e:
            logger.error("Database error while querying email logs: %s", str(e))
            raise
