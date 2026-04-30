from typing import Any
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from tuned.models import Testimonial
from tuned.dtos.content import (
    TestimonialDTO, TestimonialResponseDTO, TestimonialUpdateDTO,
    TestimonialListRequestDTO, TestimonialListResponseDTO
)
from tuned.repository.exceptions import DatabaseError, NotFound
from tuned.repository.protocols import TestimonialRepositoryProtocol

_VALID_RATINGS = frozenset(range(1, 6))


class CreateTestimonial:
    def __init__(self, session: Session) -> None:
        self.session = session

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
            self.session.add(testimonial)
            self.session.flush()
            return TestimonialResponseDTO.from_model(testimonial)
        except SQLAlchemyError as e:
            raise DatabaseError("Database error while creating testimonial.") from e


class GetTestimonialByID:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, testimonial_id: str) -> TestimonialResponseDTO:
        try:
            stmt = select(Testimonial).where(Testimonial.id == testimonial_id)
            t = self.session.scalar(stmt)
            if not t:
                raise NotFound("Testimonial not found.")
            return TestimonialResponseDTO.from_model(t)
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching testimonial: {str(e)}") from e


class GetApprovedTestimonials:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, service_id: str | None = None) -> list[TestimonialResponseDTO]:
        try:
            stmt = select(Testimonial).where(Testimonial.is_approved == True)
            if service_id:
                stmt = stmt.where(Testimonial.service_id == service_id)
            stmt = stmt.order_by(Testimonial.created_at.desc())
            testimonials = self.session.scalars(stmt).all()
            return [TestimonialResponseDTO.from_model(t) for t in testimonials]
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching testimonials: {str(e)}") from e


class GetApprovedTestimonialsPaginated:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, req: TestimonialListRequestDTO) -> TestimonialListResponseDTO:
        try:
            stmt = select(Testimonial).where(Testimonial.is_approved == True)
            if req.service_id:
                stmt = stmt.where(Testimonial.service_id == req.service_id)

            stmt = stmt.order_by(Testimonial.created_at.desc())
            
            # Count total
            count_stmt = select(func.count()).select_from(stmt.subquery())
            total = self.session.scalar(count_stmt) or 0
            
            # Paginate
            offset = (req.page - 1) * req.per_page
            stmt = stmt.offset(offset).limit(req.per_page)
            
            results = self.session.scalars(stmt).all()
            testimonials = [TestimonialResponseDTO.from_model(t) for t in results]
            
            return TestimonialListResponseDTO(
                testimonials=testimonials,
                total=total,
                page=req.page,
                per_page=req.per_page,
                sort=req.sort,
                order=req.order
            )
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching paginated testimonials: {str(e)}") from e


class GetPendingTestimonials:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self) -> list[TestimonialResponseDTO]:
        try:
            stmt = (
                select(Testimonial)
                .where(Testimonial.is_approved == False)
                .order_by(Testimonial.created_at.asc())
            )
            testimonials = self.session.scalars(stmt).all()
            return [TestimonialResponseDTO.from_model(t) for t in testimonials]
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching pending testimonials: {str(e)}") from e


class ApproveTestimonial:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, testimonial_id: str) -> TestimonialResponseDTO:
        try:
            stmt = select(Testimonial).where(Testimonial.id == testimonial_id)
            t = self.session.scalar(stmt)
            if not t:
                raise NotFound("Testimonial not found.")
            t.is_approved = True
            self.session.flush()
            return TestimonialResponseDTO.from_model(t)
        except SQLAlchemyError as e:
            raise DatabaseError("Database error while approving testimonial.") from e


class UpdateTestimonial:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, testimonial_id: str, updates: TestimonialUpdateDTO) -> TestimonialResponseDTO:
        try:
            stmt = select(Testimonial).where(Testimonial.id == testimonial_id)
            t = self.session.scalar(stmt)
            if not t:
                raise NotFound("Testimonial not found.")
            
            update_data = {k: v for k, v in updates.__dict__.items() if v is not None}
            if "rating" in update_data and update_data["rating"] not in _VALID_RATINGS:
                raise ValueError(f"Rating must be between 1 and 5, got {update_data['rating']}.")

            for key, value in update_data.items():
                if hasattr(t, key):
                    setattr(t, key, value)
            self.session.flush()
            return TestimonialResponseDTO.from_model(t)
        except SQLAlchemyError as e:
            raise DatabaseError("Database error while updating testimonial.") from e


class DeleteTestimonial:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, testimonial_id: str) -> None:
        try:
            stmt = select(Testimonial).where(Testimonial.id == testimonial_id)
            t = self.session.scalar(stmt)
            if not t:
                raise NotFound("Testimonial not found.")
            self.session.delete(t)
            self.session.flush()
        except SQLAlchemyError as e:
            raise DatabaseError("Database error while deleting testimonial.") from e

class TestimonialRepository(TestimonialRepositoryProtocol):
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, data: TestimonialDTO) -> TestimonialResponseDTO:
        return CreateTestimonial(self.session).execute(data)

    def get_by_id(self, testimonial_id: str) -> TestimonialResponseDTO:
        return GetTestimonialByID(self.session).execute(testimonial_id)

    def get_approved(self, service_id: str | None = None) -> list[TestimonialResponseDTO]:
        return GetApprovedTestimonials(self.session).execute(service_id)

    def get_approved_paginated(self, req: TestimonialListRequestDTO) -> TestimonialListResponseDTO:
        return GetApprovedTestimonialsPaginated(self.session).execute(req)

    def get_pending(self) -> list[TestimonialResponseDTO]:
        return GetPendingTestimonials(self.session).execute()

    def approve(self, testimonial_id: str) -> TestimonialResponseDTO:
        return ApproveTestimonial(self.session).execute(testimonial_id)

    def update(self, testimonial_id: str, updates: TestimonialUpdateDTO) -> TestimonialResponseDTO:
        return UpdateTestimonial(self.session).execute(testimonial_id, updates)

    def delete(self, testimonial_id: str) -> None:
        return DeleteTestimonial(self.session).execute(testimonial_id)