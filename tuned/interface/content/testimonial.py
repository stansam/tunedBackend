import logging
from typing import Optional, TYPE_CHECKING
from tuned.dtos import TestimonialDTO, TestimonialResponseDTO, TestimonialUpdateDTO
from tuned.repository.exceptions import DatabaseError, NotFound, AlreadyExists
from tuned.core.logging import get_logger

if TYPE_CHECKING:
    from tuned.repository import Repository

logger: logging.Logger = get_logger(__name__)

class TestimonialService:
    def __init__(self, repos: Optional["Repository"] = None) -> None:
        if repos:
            self._repo = repos.testimonial
        else:
            from tuned.repository import repositories
            self._repo = repositories.testimonial

    def submit_testimonial(self, data: TestimonialDTO) -> TestimonialResponseDTO:
        try:
            logger.info(
                "Submitting testimonial: user=%s service=%s rating=%d",
                data.user_id, data.service_id, data.rating,
            )
            result = self._repo.create(data)
            logger.info("Testimonial submitted: id=%s", result.id)
            return result
        except AlreadyExists:
            logger.error("Testimonial already exists: %s", data.user_id)
            raise AlreadyExists("Testimonial already exists")
        except DatabaseError:
            logger.error("Database error while submitting testimonial")
            raise DatabaseError("Database error while submitting testimonial")

    def get_testimonial(self, testimonial_id: str) -> TestimonialResponseDTO:
        try:
            return self._repo.get_by_id(testimonial_id)
        except NotFound:
            logger.error("Testimonial not found: %s", testimonial_id)
            raise NotFound("Testimonial not found")
        except DatabaseError:
            logger.error("Database error while fetching testimonial")
            raise DatabaseError("Database error while fetching testimonial")

    def list_approved_testimonials(
        self, service_id: str | None = None
    ) -> list[TestimonialResponseDTO]:
        try:
            return self._repo.get_approved(service_id=service_id)
        except DatabaseError:
            logger.error("Database error while fetching testimonials")
            raise DatabaseError("Database error while fetching testimonials")

    def list_pending_testimonials(self) -> list[TestimonialResponseDTO]:
        try:
            return self._repo.get_pending()
        except DatabaseError:
            logger.error("Database error while fetching testimonials")
            raise DatabaseError("Database error while fetching testimonials")

    def approve_testimonial(self, testimonial_id: str) -> TestimonialResponseDTO:
        try:
            logger.info("Approving testimonial id=%s", testimonial_id)
            result = self._repo.approve(testimonial_id)
            logger.info("Testimonial approved: id=%s", testimonial_id)
            return result
        except NotFound:
            logger.error("Testimonial not found: %s", testimonial_id)
            raise NotFound("Testimonial not found")
        except DatabaseError:
            logger.error("Database error while approving testimonial")
            raise DatabaseError("Database error while approving testimonial")

    def update_testimonial(self, testimonial_id: str, updates: TestimonialUpdateDTO) -> TestimonialResponseDTO:
        try:
            logger.info("Updating testimonial id=%s", testimonial_id)
            result = self._repo.update(testimonial_id, updates)
            logger.info("Testimonial updated: id=%s", testimonial_id)
            return result
        except NotFound:
            logger.error("Testimonial not found: %s", testimonial_id)
            raise NotFound("Testimonial not found")
        except DatabaseError:
            logger.error("Database error while updating testimonial")
            raise DatabaseError("Database error while updating testimonial")

    def delete_testimonial(self, testimonial_id: str) -> None:
        try:
            logger.info("Deleting testimonial id=%s", testimonial_id)
            self._repo.delete(testimonial_id)
            logger.info("Testimonial deleted: id=%s", testimonial_id)
        except NotFound:
            logger.error("Testimonial not found: %s", testimonial_id)
            raise NotFound("Testimonial not found")
        except DatabaseError:
            logger.error("Database error while deleting testimonial")
            raise DatabaseError("Database error while deleting testimonial")
