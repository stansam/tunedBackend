from sqlalchemy.orm import Session
from sqlalchemy import func, select, update
from sqlalchemy.exc import SQLAlchemyError
from tuned.models.communication import Notification
from tuned.dtos.notification import NotificationCreateDTO, NotificationResponseDTO
from tuned.repository.exceptions import DatabaseError, NotFound
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
            self.session.flush()
            return NotificationResponseDTO.from_model(notification)
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while creating notification: {str(e)}") from e

    def get_unread_count(self, user_id: str) -> int:
        try:
            stmt = select(func.count(Notification.id)).where(
                Notification.user_id == user_id,
                Notification.is_read.is_(False),
            )
            return self.session.scalar(stmt) or 0
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error: {str(e)}") from e

    def mark_read(self, notification_id: str, user_id: str) -> NotificationResponseDTO:
        try:
            notification = self._get_by_id_for_user(notification_id, user_id)
            if not notification:
                raise NotFound("Notification not found")
            notification.is_read = True
            self.session.flush()
            return NotificationResponseDTO.from_model(notification)
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error: {str(e)}") from e

    def mark_all_read(self, user_id: str) -> int:
        try:
            unread_count = self.get_unread_count(user_id)
            stmt = (
                update(Notification)
                .where(
                    Notification.user_id == user_id,
                    Notification.is_read.is_(False),
                )
                .values(is_read=True)
            )
            self.session.execute(stmt)
            return unread_count
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error: {str(e)}") from e

    def get_user_notifications(
        self,
        user_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> list[NotificationResponseDTO]:
        try:
            stmt = (
                select(Notification)
                .where(Notification.user_id == user_id)
                .order_by(Notification.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            notifications = self.session.scalars(stmt).all()
            return [NotificationResponseDTO.from_model(item) for item in notifications]
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error: {str(e)}") from e

    def save(self) -> None:
        try:
            self.session.commit()
        except SQLAlchemyError as e:
            self.session.rollback()
            raise DatabaseError(f"Database error while saving notifications: {str(e)}") from e

    def rollback(self) -> None:
        self.session.rollback()

    def _get_by_id_for_user(self, notification_id: str, user_id: str) -> Notification | None:
        stmt = select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == user_id,
        )
        return self.session.scalar(stmt)
