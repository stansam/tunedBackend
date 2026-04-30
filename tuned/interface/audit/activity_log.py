from __future__ import annotations
import logging
from tuned.dtos import ActivityLogCreateDTO, ActivityLogResponseDTO, ActivityLogFilterDTO, AuditListResponseDTO
from tuned.repository.exceptions import DatabaseError, NotFound
from tuned.core.logging import get_logger
from tuned.utils.audit import sanitize_json_snapshot, sanitize_ip, truncate_user_agent
from typing import List, Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from tuned.repository import Repository
    from tuned.repository.protocols.audit import ActivityLogRepositoryProtocol

logger: logging.Logger = get_logger(__name__)

class ActivityLogService:
    def __init__(self, repos: Repository) -> None:
        self._repo = repos.audit.activity_log

    def log(self, data: ActivityLogCreateDTO) -> ActivityLogResponseDTO:
        try:
            logger.info("Logging activity: %s", data.action)
            
            data.before = sanitize_json_snapshot(data.before)
            data.after = sanitize_json_snapshot(data.after)
            data.ip_address = sanitize_ip(data.ip_address)
            data.user_agent = truncate_user_agent(data.user_agent)
            
            return self._repo.create(data)
        except DatabaseError as e:
            logger.error("Database error while logging activity: %s", str(e))
            raise

    def get_log(self, log_id: str) -> ActivityLogResponseDTO:
        try:
            return self._repo.get_by_id(log_id)
        except NotFound:
            logger.error("Activity log record not found: %s", log_id)
            raise
        except DatabaseError as e:
            logger.error("Database error while fetching activity log: %s", str(e))
            raise

    def query_logs(self, filters: ActivityLogFilterDTO) -> AuditListResponseDTO[ActivityLogResponseDTO]:
        try:
            items, total = self._repo.get_filtered(filters)
            return AuditListResponseDTO[ActivityLogResponseDTO](
                items=list(items),
                total=total,
                page=filters.page,
                per_page=filters.per_page
            )
        except DatabaseError as e:
            logger.error("Database error while querying activity logs: %s", str(e))
            raise

    def query_user_logs(self, user_id: str, page: int = 1, per_page: int = 20) -> AuditListResponseDTO[ActivityLogResponseDTO]:
        filters = ActivityLogFilterDTO(user_id=user_id, page=page, per_page=per_page)
        return self.query_logs(filters)

    def query_entity_logs(self, entity_type: str, entity_id: str) -> List[ActivityLogResponseDTO]:
        filters = ActivityLogFilterDTO(entity_type=entity_type, entity_id=entity_id, per_page=100)
        items, _ = self._repo.get_filtered(filters)
        return list(items)
