from typing import Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from tuned.extensions import db
from tuned.models import FAQ
from tuned.dtos.content import FaqDTO, FaqResponseDTO
from tuned.repository.exceptions import AlreadyExists, DatabaseError, NotFound


class CreateFAQ:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, data: FaqDTO) -> FaqResponseDTO:
        try:
            faq = FAQ(
                question=data.question,
                answer=data.answer,
                category=data.category,
                order=data.order,
            )
            self.session.add(faq)
            self.session.commit()
            return FaqResponseDTO.from_model(faq)
        except IntegrityError:
            self.session.rollback()
            raise AlreadyExists("A FAQ with this question already exists.")
        except SQLAlchemyError as e:
            self.session.rollback()
            raise DatabaseError("Database error while creating FAQ.") from e


class GetFAQByID:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, faq_id: str) -> FaqResponseDTO:
        try:
            faq = self.session.query(FAQ).filter_by(id=faq_id).first()
            if not faq:
                raise NotFound("FAQ not found.")
            return FaqResponseDTO.from_model(faq)
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching FAQ: {str(e)}") from e


class GetAllFAQs:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, category: str | None = None) -> list[FaqResponseDTO]:
        try:
            query = self.session.query(FAQ)
            if category:
                query = query.filter_by(category=category)
            faqs = query.order_by(FAQ.category.asc(), FAQ.order.asc()).all()
            return [FaqResponseDTO.from_model(f) for f in faqs]
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching FAQs: {str(e)}") from e


class GetFAQCategories:
    """Return the distinct category values for navigation/filtering."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self) -> list[str]:
        try:
            rows = (
                self.session.query(FAQ.category)
                .distinct()
                .order_by(FAQ.category.asc())
                .all()
            )
            return [row[0] for row in rows]
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching FAQ categories: {str(e)}") from e


class UpdateFAQ:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, faq_id: str, updates: dict[str, Any]) -> FaqResponseDTO:
        try:
            faq = self.session.query(FAQ).filter_by(id=faq_id).first()
            if not faq:
                raise NotFound("FAQ not found.")
            for key, value in updates.items():
                if hasattr(faq, key):
                    setattr(faq, key, value)
            self.session.commit()
            return FaqResponseDTO.from_model(faq)
        except IntegrityError:
            self.session.rollback()
            raise AlreadyExists("A FAQ with that question already exists.")
        except SQLAlchemyError as e:
            self.session.rollback()
            raise DatabaseError("Database error while updating FAQ.") from e


class DeleteFAQ:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, faq_id: str) -> None:
        try:
            faq = self.session.query(FAQ).filter_by(id=faq_id).first()
            if not faq:
                raise NotFound("FAQ not found.")
            self.session.delete(faq)
            self.session.commit()
        except SQLAlchemyError as e:
            self.session.rollback()
            raise DatabaseError("Database error while deleting FAQ.") from e


class FAQRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, data: FaqDTO) -> FaqResponseDTO:
        return CreateFAQ(self.session).execute(data)

    def get_by_id(self, faq_id: str) -> FaqResponseDTO:
        return GetFAQByID(self.session).execute(faq_id)

    def get_all(self, category: str | None = None) -> list[FaqResponseDTO]:
        return GetAllFAQs(self.session).execute(category)

    def get_categories(self) -> list[str]:
        return GetFAQCategories(self.session).execute()

    def update(self, faq_id: str, updates: dict[str, Any]) -> FaqResponseDTO:
        return UpdateFAQ(self.session).execute(faq_id, updates)

    def delete(self, faq_id: str) -> None:
        return DeleteFAQ(self.session).execute(faq_id)
