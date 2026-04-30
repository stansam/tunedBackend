from typing import Any
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from tuned.models import FAQ
from tuned.dtos.content import FaqDTO, FaqResponseDTO, FaqUpdateDTO
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
            self.session.flush()
            return FaqResponseDTO.from_model(faq)
        except IntegrityError:
            raise AlreadyExists("A FAQ with this question already exists.")
        except SQLAlchemyError as e:
            raise DatabaseError("Database error while creating FAQ.") from e


class GetFAQByID:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, faq_id: str) -> FaqResponseDTO:
        try:
            stmt = select(FAQ).where(FAQ.id == faq_id)
            faq = self.session.scalar(stmt)
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
            stmt = select(FAQ)
            if category:
                stmt = stmt.where(FAQ.category == category)
            stmt = stmt.order_by(FAQ.category.asc(), FAQ.order.asc())
            faqs = self.session.scalars(stmt).all()
            return [FaqResponseDTO.from_model(f) for f in faqs]
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching FAQs: {str(e)}") from e


class GetFAQCategories:
    """Return the distinct category values for navigation/filtering."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self) -> list[str]:
        try:
            stmt = (
                select(FAQ.category)
                .distinct()
                .order_by(FAQ.category.asc())
            )
            rows = self.session.execute(stmt).all()
            return [row[0] for row in rows]
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching FAQ categories: {str(e)}") from e


class UpdateFAQ:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, faq_id: str, updates: FaqUpdateDTO) -> FaqResponseDTO:
        try:
            stmt = select(FAQ).where(FAQ.id == faq_id)
            faq = self.session.scalar(stmt)
            if not faq:
                raise NotFound("FAQ not found.")
            update_data = {k: v for k, v in updates.__dict__.items() if v is not None}
            for key, value in update_data.items():
                if hasattr(faq, key):
                    setattr(faq, key, value)
            self.session.flush()
            return FaqResponseDTO.from_model(faq)
        except IntegrityError:
            raise AlreadyExists("A FAQ with that question already exists.")
        except SQLAlchemyError as e:
            raise DatabaseError("Database error while updating FAQ.") from e


class DeleteFAQ:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, faq_id: str) -> None:
        try:
            stmt = select(FAQ).where(FAQ.id == faq_id)
            faq = self.session.scalar(stmt)
            if not faq:
                raise NotFound("FAQ not found.")
            self.session.delete(faq)
            self.session.flush()
        except SQLAlchemyError as e:
            raise DatabaseError("Database error while deleting FAQ.") from e


from tuned.repository.protocols import FAQRepositoryProtocol

class FAQRepository(FAQRepositoryProtocol):
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

    def update(self, faq_id: str, updates: FaqUpdateDTO) -> FaqResponseDTO:
        return UpdateFAQ(self.session).execute(faq_id, updates)

    def delete(self, faq_id: str) -> None:
        return DeleteFAQ(self.session).execute(faq_id)
