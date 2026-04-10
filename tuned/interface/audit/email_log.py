import logging
from tuned.dtos import EmailLogCreateDTO, EmailLogResponseDTO, EmailLogFilterDTO, EmailLogUpdateDTO, AuditListResponseDTO
from tuned.repository import repositories
from tuned.repository.exceptions import DatabaseError, NotFound
from tuned.core.logging import get_logger

logger: logging.Logger = get_logger(__name__)

class EmailLogService:
    def __init__(self) -> None:
        self._repo = repositories.audit.email_log

    def log_email(self, data: EmailLogCreateDTO) -> EmailLogResponseDTO:
        try:
            logger.info("Logging email attempt to: %s", data.recipient)
            return self._repo.create(data)
        except DatabaseError as e:
            logger.error("Database error while logging email: %s", str(e))
            raise

    def mark_sent(self, log_id: str) -> EmailLogResponseDTO:
        try:
            logger.info("Marking email log as sent: %s", log_id)
            return self._repo.update_status(log_id, EmailLogUpdateDTO(status="sent"))
        except (NotFound, DatabaseError) as e:
            logger.error("Error marking email as sent: %s", str(e))
            raise

    def mark_failed(self, log_id: str, error_message: str) -> EmailLogResponseDTO:
        try:
            logger.info("Marking email log as failed: %s", log_id)
            return self._repo.update_status(log_id, EmailLogUpdateDTO(status="failed", error_message=error_message))
        except (NotFound, DatabaseError) as e:
            logger.error("Error marking email as failed: %s", str(e))
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

    def query_logs(self, filters: EmailLogFilterDTO) -> AuditListResponseDTO[EmailLogResponseDTO]:
        try:
            items, total = self._repo.get_filtered(filters)
            return AuditListResponseDTO[EmailLogResponseDTO](
                items=items,
                total=total,
                page=filters.page,
                per_page=filters.per_page
            )
        except DatabaseError as e:
            logger.error("Database error while querying email logs: %s", str(e))
            raise
