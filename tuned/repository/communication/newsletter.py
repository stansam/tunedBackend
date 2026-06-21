from sqlalchemy.orm import Session
from sqlalchemy import select
from tuned.models.communication import NewsletterSubscriber
from tuned.dtos.communication import NewsletterSubscribeDTO, NewsletterSubscriberResponseDTO
from tuned.repository.exceptions import DatabaseError, NotFound
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional

class NewsletterRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_email(self, email: str) -> Optional[NewsletterSubscriber]:
        try:
            stmt = select(NewsletterSubscriber).where(NewsletterSubscriber.email == email)
            subscriber = self.session.scalar(stmt)
            if not subscriber:
                return None
            return subscriber
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching subscriber: {str(e)}") from e

    def create(self, data: NewsletterSubscribeDTO) -> NewsletterSubscriber:
        try:
            subscriber = NewsletterSubscriber(
                email=data.email,
                name=data.name,
                is_active=True
            )
            self.session.add(subscriber)
            self.session.flush()
            return subscriber
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while creating subscriber: {str(e)}") from e

    def update_status(self, subscriber_id: str, is_active: bool, name: Optional[str] = None) -> NewsletterSubscriber:
        try:
            stmt = select(NewsletterSubscriber).where(NewsletterSubscriber.id == subscriber_id)
            subscriber = self.session.scalar(stmt)
            if not subscriber:
                raise NotFound("Subscriber not found")
            
            subscriber.is_active = is_active
            if name:
                subscriber.name = name
                
            self.session.flush()
            return subscriber
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while updating subscriber: {str(e)}") from e

    def save(self) -> None:
        try:
            self.session.commit()
        except SQLAlchemyError as e:
            self.session.rollback()
            raise DatabaseError(f"Database error while saving: {str(e)}") from e
        
    def rollback(self) -> None:
        self.session.rollback()