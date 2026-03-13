from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from tuned.extensions import db
from tuned.models import FAQ
from tuned.dtos.content import FaqDTO, FaqResponseDTO
from tuned.repository.exceptions import AlreadyExists, DatabaseError, NotFound


class CreateFAQ:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, data: FaqDTO) -> FaqResponseDTO:
        try:
            faq = FAQ(
                question=data.question,
                answer=data.answer,
                category=data.category,
                order=data.order,
            )
            self.db.session.add(faq)
            self.db.session.commit()
            return FaqResponseDTO.from_model(faq)
        except IntegrityError:
            self.db.session.rollback()
            raise AlreadyExists("A FAQ with this question already exists.")
        except SQLAlchemyError as e:
            self.db.session.rollback()
            raise DatabaseError("Database error while creating FAQ.") from e


class GetFAQByID:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, faq_id: str) -> FaqResponseDTO:
        try:
            faq = self.db.session.query(FAQ).filter_by(id=faq_id).first()
            if not faq:
                raise NotFound("FAQ not found.")
            return FaqResponseDTO.from_model(faq)
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching FAQ: {str(e)}") from e


class GetAllFAQs:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, category: str | None = None) -> list[FaqResponseDTO]:
        try:
            query = self.db.session.query(FAQ)
            if category:
                query = query.filter_by(category=category)
            faqs = query.order_by(FAQ.category.asc(), FAQ.order.asc()).all()
            return [FaqResponseDTO.from_model(f) for f in faqs]
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching FAQs: {str(e)}") from e


class GetFAQCategories:
    """Return the distinct category values for navigation/filtering."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self) -> list[str]:
        try:
            rows = (
                self.db.session.query(FAQ.category)
                .distinct()
                .order_by(FAQ.category.asc())
                .all()
            )
            return [row[0] for row in rows]
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching FAQ categories: {str(e)}") from e


class UpdateFAQ:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, faq_id: str, updates: dict) -> FaqResponseDTO:
        try:
            faq = self.db.session.query(FAQ).filter_by(id=faq_id).first()
            if not faq:
                raise NotFound("FAQ not found.")
            for key, value in updates.items():
                if hasattr(faq, key):
                    setattr(faq, key, value)
            self.db.session.commit()
            return FaqResponseDTO.from_model(faq)
        except IntegrityError:
            self.db.session.rollback()
            raise AlreadyExists("A FAQ with that question already exists.")
        except SQLAlchemyError as e:
            self.db.session.rollback()
            raise DatabaseError("Database error while updating FAQ.") from e


class DeleteFAQ:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, faq_id: str) -> None:
        try:
            faq = self.db.session.query(FAQ).filter_by(id=faq_id).first()
            if not faq:
                raise NotFound("FAQ not found.")
            self.db.session.delete(faq)
            self.db.session.commit()
        except SQLAlchemyError as e:
            self.db.session.rollback()
            raise DatabaseError("Database error while deleting FAQ.") from e


class FAQRepository:
    """Facade composing all FAQ command objects."""

    def __init__(self) -> None:
        self.db = db

    def create(self, data: FaqDTO) -> FaqResponseDTO:
        return CreateFAQ(self.db).execute(data)

    def get_by_id(self, faq_id: str) -> FaqResponseDTO:
        return GetFAQByID(self.db).execute(faq_id)

    def get_all(self, category: str | None = None) -> list[FaqResponseDTO]:
        return GetAllFAQs(self.db).execute(category)

    def get_categories(self) -> list[str]:
        return GetFAQCategories(self.db).execute()

    def update(self, faq_id: str, updates: dict) -> FaqResponseDTO:
        return UpdateFAQ(self.db).execute(faq_id, updates)

    def delete(self, faq_id: str) -> None:
        return DeleteFAQ(self.db).execute(faq_id)
