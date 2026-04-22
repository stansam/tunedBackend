from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from tuned.models.communication import Notification
from tuned.dtos.notification import NotificationCreateDTO, NotificationResponseDTO
from tuned.repository.exceptions import DatabaseError, NotFound
from typing import List
from datetime import datetime, timezone
class NotificationRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, data: NotificationCreateDTO) -> NotificationResponseDTO:
        try:
            notification = Notification(
                user_id=data.user_id,
                title=data.title,
                message=data.message,
                type=data.notification_type,
                link=data.link,
                is_read=False,
                created_at=datetime.now(timezone.utc),
                created_by=data.user_id

            )
            self.session.add(notification)
            self.session.commit()
            self.session.refresh(notification)
            return NotificationResponseDTO.from_model(notification)
        except SQLAlchemyError as e:
            self.session.rollback()
            raise DatabaseError(f"Database error while creating notification: {str(e)}") from e

    def get_unread_count(self, user_id: str) -> int:
        try:
            return self.session.query(Notification).filter_by(
                user_id=user_id,
                is_read=False
            ).count()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error: {str(e)}") from e

    def mark_read(self, notification_id: str) -> bool:
        try:
            notification = self.session.query(Notification).filter_by(id=notification_id).first()
            if not notification:
                raise NotFound("Notification not found")
            notification.is_read = True
            self.session.commit()
            return True
        except SQLAlchemyError as e:
            self.session.rollback()
            raise DatabaseError(f"Database error: {str(e)}") from e

    def mark_all_read(self, user_id: str) -> int:
        try:
            count = self.session.query(Notification).filter_by(
                user_id=user_id,
                is_read=False
            ).update({'is_read': True})
            self.session.commit()
            return count
        except SQLAlchemyError as e:
            self.session.rollback()
            raise DatabaseError(f"Database error: {str(e)}") from e

    def get_user_notifications(self, user_id: str, limit: int = 20, offset: int = 0) -> List[Notification]:
        try:
            return self.session.query(Notification).filter_by(
                user_id=user_id
            ).order_by(Notification.created_at.desc()).limit(limit).offset(offset).all()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error: {str(e)}") from e
