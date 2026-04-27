from sqlalchemy.orm import Session
from sqlalchemy import select, func
from sqlalchemy.exc import SQLAlchemyError
from tuned.models import ActivityLog
from tuned.dtos import ActivityLogCreateDTO, ActivityLogResponseDTO, ActivityLogFilterDTO
from tuned.repository.exceptions import DatabaseError, NotFound

class CreateActivityLog:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, data: ActivityLogCreateDTO) -> ActivityLogResponseDTO:
        try:
            log = ActivityLog(
                user_id=data.user_id,
                action=data.action,
                entity_type=data.entity_type,
                entity_id=data.entity_id,
                before=data.before,
                after=data.after,
                ip_address=data.ip_address,
                user_agent=data.user_agent
            )
            self.session.add(log)
            self.session.flush()
            return ActivityLogResponseDTO.from_model(log)
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while creating activity log: {str(e)}") from e

class GetActivityLogByID:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, log_id: str) -> ActivityLogResponseDTO:
        try:
            stmt = select(ActivityLog).where(ActivityLog.id == log_id)
            log = self.session.scalar(stmt)
            if not log:
                raise NotFound("Activity log record not found.")
            return ActivityLogResponseDTO.from_model(log)
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching log: {str(e)}") from e

class GetActivityLogsFiltered:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, filters: ActivityLogFilterDTO) -> tuple[list[ActivityLogResponseDTO], int]:
        try:
            stmt = select(ActivityLog)
            
            if filters.user_id:
                stmt = stmt.where(ActivityLog.user_id == filters.user_id)
            if filters.action:
                stmt = stmt.where(ActivityLog.action == filters.action)
            if filters.entity_type:
                stmt = stmt.where(ActivityLog.entity_type == filters.entity_type)
            if filters.entity_id:
                stmt = stmt.where(ActivityLog.entity_id == filters.entity_id)
            
            # Count total
            count_stmt = select(func.count()).select_from(stmt.subquery())
            total = self.session.scalar(count_stmt) or 0
            
            sort_attr = getattr(ActivityLog, filters.sort, ActivityLog.created_at)
            if filters.order == "desc":
                stmt = stmt.order_by(sort_attr.desc())
            else:
                stmt = stmt.order_by(sort_attr.asc())
                
            stmt = stmt.offset((filters.page - 1) * filters.per_page).limit(filters.per_page)
            items = self.session.scalars(stmt).all()
            
            return [ActivityLogResponseDTO.from_model(i) for i in items], total
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching activity logs: {str(e)}") from e

class ActivityLogRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, data: ActivityLogCreateDTO) -> ActivityLogResponseDTO:
        return CreateActivityLog(self.session).execute(data)

    def get_by_id(self, log_id: str) -> ActivityLogResponseDTO:
        return GetActivityLogByID(self.session).execute(log_id)

    def get_filtered(self, filters: ActivityLogFilterDTO) -> tuple[list[ActivityLogResponseDTO], int]:
        return GetActivityLogsFiltered(self.session).execute(filters)
