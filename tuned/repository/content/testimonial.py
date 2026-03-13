from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from tuned.extensions import db
from tuned.models import Testimonial
from tuned.dtos.content import TestimonialDTO, TestimonialResponseDTO
from tuned.repository.exceptions import DatabaseError, NotFound


_VALID_RATINGS = frozenset(range(1, 6))


class CreateTestimonial:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, data: TestimonialDTO) -> TestimonialResponseDTO:
        if data.rating not in _VALID_RATINGS:
            raise ValueError(f"Rating must be between 1 and 5, got {data.rating}.")
        try:
            testimonial = Testimonial(
                user_id=data.user_id,
                service_id=data.service_id,
                order_id=data.order_id,
                content=data.content,
                rating=data.rating,
                is_approved=data.is_approved,
            )
            self.db.session.add(testimonial)
            self.db.session.commit()
            return TestimonialResponseDTO.from_model(testimonial)
        except SQLAlchemyError as e:
            self.db.session.rollback()
            raise DatabaseError("Database error while creating testimonial.") from e


class GetTestimonialByID:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, testimonial_id: str) -> TestimonialResponseDTO:
        try:
            t = self.db.session.query(Testimonial).filter_by(id=testimonial_id).first()
            if not t:
                raise NotFound("Testimonial not found.")
            return TestimonialResponseDTO.from_model(t)
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching testimonial: {str(e)}") from e


class GetApprovedTestimonials:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, service_id: str | None = None) -> list[TestimonialResponseDTO]:
        try:
            query = self.db.session.query(Testimonial).filter_by(is_approved=True)
            if service_id:
                query = query.filter_by(service_id=service_id)
            testimonials = query.order_by(Testimonial.created_at.desc()).all()
            return [TestimonialResponseDTO.from_model(t) for t in testimonials]
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching testimonials: {str(e)}") from e


class GetPendingTestimonials:
    """Admin-only — fetch unapproved testimonials awaiting moderation."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self) -> list[TestimonialResponseDTO]:
        try:
            testimonials = (
                self.db.session.query(Testimonial)
                .filter_by(is_approved=False)
                .order_by(Testimonial.created_at.asc())
                .all()
            )
            return [TestimonialResponseDTO.from_model(t) for t in testimonials]
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching pending testimonials: {str(e)}") from e


class ApproveTestimonial:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, testimonial_id: str) -> TestimonialResponseDTO:
        try:
            t = self.db.session.query(Testimonial).filter_by(id=testimonial_id).first()
            if not t:
                raise NotFound("Testimonial not found.")
            t.is_approved = True
            self.db.session.commit()
            return TestimonialResponseDTO.from_model(t)
        except SQLAlchemyError as e:
            self.db.session.rollback()
            raise DatabaseError("Database error while approving testimonial.") from e


class UpdateTestimonial:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, testimonial_id: str, updates: dict) -> TestimonialResponseDTO:
        if "rating" in updates and updates["rating"] not in _VALID_RATINGS:
            raise ValueError(f"Rating must be between 1 and 5, got {updates['rating']}.")
        try:
            t = self.db.session.query(Testimonial).filter_by(id=testimonial_id).first()
            if not t:
                raise NotFound("Testimonial not found.")
            for key, value in updates.items():
                if hasattr(t, key):
                    setattr(t, key, value)
            self.db.session.commit()
            return TestimonialResponseDTO.from_model(t)
        except SQLAlchemyError as e:
            self.db.session.rollback()
            raise DatabaseError("Database error while updating testimonial.") from e


class DeleteTestimonial:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, testimonial_id: str) -> None:
        try:
            t = self.db.session.query(Testimonial).filter_by(id=testimonial_id).first()
            if not t:
                raise NotFound("Testimonial not found.")
            self.db.session.delete(t)
            self.db.session.commit()
        except SQLAlchemyError as e:
            self.db.session.rollback()
            raise DatabaseError("Database error while deleting testimonial.") from e


class TestimonialRepository:
    """Facade composing all Testimonial command objects."""

    def __init__(self) -> None:
        self.db = db

    def create(self, data: TestimonialDTO) -> TestimonialResponseDTO:
        return CreateTestimonial(self.db).execute(data)

    def get_by_id(self, testimonial_id: str) -> TestimonialResponseDTO:
        return GetTestimonialByID(self.db).execute(testimonial_id)

    def get_approved(self, service_id: str | None = None) -> list[TestimonialResponseDTO]:
        return GetApprovedTestimonials(self.db).execute(service_id)

    def get_pending(self) -> list[TestimonialResponseDTO]:
        return GetPendingTestimonials(self.db).execute()

    def approve(self, testimonial_id: str) -> TestimonialResponseDTO:
        return ApproveTestimonial(self.db).execute(testimonial_id)

    def update(self, testimonial_id: str, updates: dict) -> TestimonialResponseDTO:
        return UpdateTestimonial(self.db).execute(testimonial_id, updates)

    def delete(self, testimonial_id: str) -> None:
        return DeleteTestimonial(self.db).execute(testimonial_id)