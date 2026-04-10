from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from tuned.models import EmailLog
from tuned.dtos import EmailLogCreateDTO, EmailLogResponseDTO, EmailLogFilterDTO, EmailLogUpdateDTO
from tuned.repository.exceptions import DatabaseError, NotFound

class CreateEmailLog:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, data: EmailLogCreateDTO) -> EmailLogResponseDTO:
        try:
            log = EmailLog(
                recipient=data.recipient,
                subject=data.subject,
                template=data.template,
                user_id=data.user_id,
                order_id=data.order_id,
                status="pending"
            )
            self.db.add(log)
            self.db.commit()
            self.db.refresh(log)
            return EmailLogResponseDTO.from_model(log)
        except SQLAlchemyError as e:
            self.db.rollback()
            raise DatabaseError(f"Database error while creating email log: {str(e)}") from e

class GetEmailLogByID:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, log_id: str) -> EmailLogResponseDTO:
        try:
            log = self.db.query(EmailLog).filter_by(id=log_id).first()
            if not log:
                raise NotFound("Email log record not found.")
            return EmailLogResponseDTO.from_model(log)
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching email log: {str(e)}") from e

class GetEmailLogsFiltered:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, filters: EmailLogFilterDTO) -> tuple[list[EmailLogResponseDTO], int]:
        try:
            query = self.db.query(EmailLog)
            
            if filters.recipient:
                query = query.filter(EmailLog.recipient.ilike(f"%{filters.recipient}%"))
            if filters.status:
                query = query.filter_by(status=filters.status)
            if filters.user_id:
                query = query.filter_by(user_id=filters.user_id)
            if filters.order_id:
                query = query.filter_by(order_id=filters.order_id)
                
            total = query.count()
            items = query.order_by(EmailLog.created_at.desc()).offset((filters.page - 1) * filters.per_page).limit(filters.per_page).all()
            return [EmailLogResponseDTO.from_model(i) for i in items], total
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching email logs: {str(e)}") from e

class UpdateEmailLogStatus:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, log_id: str, data: EmailLogUpdateDTO) -> EmailLogResponseDTO:
        try:
            log = self.db.query(EmailLog).filter_by(id=log_id).first()
            if not log:
                raise NotFound("Email log record not found.")
            
            log.status = data.status
            if data.error_message:
                log.error_message = data.error_message
            if data.sent_at:
                log.sent_at = data.sent_at
            elif data.status == "sent":
                log.sent_at = datetime.now(timezone.utc)
                
            self.db.add(log)
            self.db.commit()
            self.db.refresh(log)
            return EmailLogResponseDTO.from_model(log)
        except SQLAlchemyError as e:
            self.db.rollback()
            raise DatabaseError(f"Database error while updating email log status: {str(e)}") from e

class EmailLogRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, data: EmailLogCreateDTO) -> EmailLogResponseDTO:
        return CreateEmailLog(self.session).execute(data)

    def get_by_id(self, log_id: str) -> EmailLogResponseDTO:
        return GetEmailLogByID(self.session).execute(log_id)

    def get_filtered(self, filters: EmailLogFilterDTO) -> tuple[list[EmailLogResponseDTO], int]:
        return GetEmailLogsFiltered(self.session).execute(filters)

    def update_status(self, log_id: str, data: EmailLogUpdateDTO) -> EmailLogResponseDTO:
        return UpdateEmailLogStatus(self.session).execute(log_id, data)
