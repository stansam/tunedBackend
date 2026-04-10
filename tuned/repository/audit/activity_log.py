from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from tuned.models import ActivityLog
from tuned.dtos import ActivityLogCreateDTO, ActivityLogResponseDTO, ActivityLogFilterDTO
from tuned.repository.exceptions import DatabaseError, NotFound

class CreateActivityLog:
    def __init__(self, db: Session) -> None:
        self.db = db

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
            self.db.add(log)
            self.db.commit()
            self.db.refresh(log)
            return ActivityLogResponseDTO.from_model(log)
        except SQLAlchemyError as e:
            self.db.rollback()
            raise DatabaseError(f"Database error while creating activity log: {str(e)}") from e

class GetActivityLogByID:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, log_id: str) -> ActivityLogResponseDTO:
        try:
            log = self.db.query(ActivityLog).filter_by(id=log_id).first()
            if not log:
                raise NotFound("Activity log record not found.")
            return ActivityLogResponseDTO.from_model(log)
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching log: {str(e)}") from e

class GetActivityLogsFiltered:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, filters: ActivityLogFilterDTO) -> tuple[list[ActivityLogResponseDTO], int]:
        try:
            query = self.db.query(ActivityLog)
            
            if filters.user_id:
                query = query.filter_by(user_id=filters.user_id)
            if filters.action:
                query = query.filter_by(action=filters.action)
            if filters.entity_type:
                query = query.filter_by(entity_type=filters.entity_type)
            if filters.entity_id:
                query = query.filter_by(entity_id=filters.entity_id)
                
            total = query.count()
            
            sort_attr = getattr(ActivityLog, filters.sort, ActivityLog.created_at)
            if filters.order == "desc":
                query = query.order_by(sort_attr.desc())
            else:
                query = query.order_by(sort_attr.asc())
                
            items = query.offset((filters.page - 1) * filters.per_page).limit(filters.per_page).all()
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
