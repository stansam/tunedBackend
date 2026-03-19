import logging

from tuned.dtos import TestimonialDTO, TestimonialResponseDTO
from tuned.repository import repositories
from tuned.repository.exceptions import DatabaseError, NotFound

logger = logging.getLogger(__name__)


class TestimonialService:
    """Service layer for Testimonial business logic including moderation."""

    def __init__(self) -> None:
        self._repo = repositories.testimonial

    def submit_testimonial(self, data: TestimonialDTO) -> TestimonialResponseDTO:
        """Submit a new client testimonial (pending moderation by default).

        Raises:
            ValueError: If rating is outside the 1–5 range.
            DatabaseError: On unexpected database failure.
        """
        logger.info(
            "Submitting testimonial: user=%s service=%s rating=%d",
            data.user_id, data.service_id, data.rating,
        )
        result = self._repo.create(data)
        logger.info("Testimonial submitted: id=%s", result.id)
        return result

    def get_testimonial(self, testimonial_id: str) -> TestimonialResponseDTO:
        """Retrieve a testimonial by ID.

        Raises:
            NotFound: If no testimonial exists with the given ID.
            DatabaseError: On unexpected database failure.
        """
        return self._repo.get_by_id(testimonial_id)

    def list_approved_testimonials(
        self, service_id: str | None = None
    ) -> list[TestimonialResponseDTO]:
        """Return all approved (publicly visible) testimonials.

        Args:
            service_id: Optionally filter by service.

        Raises:
            DatabaseError: On unexpected database failure.
        """
        return self._repo.get_approved(service_id=service_id)

    def list_pending_testimonials(self) -> list[TestimonialResponseDTO]:
        """Admin — return all testimonials awaiting moderation.

        Raises:
            DatabaseError: On unexpected database failure.
        """
        return self._repo.get_pending()

    def approve_testimonial(self, testimonial_id: str) -> TestimonialResponseDTO:
        """Mark a testimonial as approved for public display.

        Raises:
            NotFound: If no testimonial exists with the given ID.
            DatabaseError: On unexpected database failure.
        """
        logger.info("Approving testimonial id=%s", testimonial_id)
        result = self._repo.approve(testimonial_id)
        logger.info("Testimonial approved: id=%s", testimonial_id)
        return result

    def update_testimonial(self, testimonial_id: str, updates: dict) -> TestimonialResponseDTO:
        """Update mutable fields of a testimonial.

        Raises:
            NotFound: If no testimonial exists with the given ID.
            ValueError: If rating is outside 1–5.
            DatabaseError: On unexpected database failure.
        """
        allowed = {"content", "rating", "is_approved"}
        safe_updates = {k: v for k, v in updates.items() if k in allowed}
        logger.info("Updating testimonial id=%s fields=%s", testimonial_id, list(safe_updates.keys()))
        result = self._repo.update(testimonial_id, safe_updates)
        logger.info("Testimonial updated: id=%s", testimonial_id)
        return result

    def delete_testimonial(self, testimonial_id: str) -> None:
        """Permanently delete a testimonial.

        Raises:
            NotFound: If no testimonial exists with the given ID.
            DatabaseError: On unexpected database failure.
        """
        logger.info("Deleting testimonial id=%s", testimonial_id)
        self._repo.delete(testimonial_id)
        logger.info("Testimonial deleted: id=%s", testimonial_id)
