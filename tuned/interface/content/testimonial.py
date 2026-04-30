from __future__ import annotations
import logging
from typing import Optional, TYPE_CHECKING

from tuned.dtos import TestimonialDTO, TestimonialResponseDTO
from tuned.repository.exceptions import AlreadyExists, DatabaseError, NotFound
from tuned.core.logging import get_logger

if TYPE_CHECKING:
    from tuned.repository import Repository

logger: logging.Logger = get_logger(__name__)


class TestimonialService:
    """Service layer for client testimonial business logic."""

    def __init__(self, repos: Optional[Repository] = None) -> None:
        if repos:
            self._repo = repos.testimonial
        else:
            from tuned.repository import repositories
            self._repo = repositories.testimonial

    def create_testimonial(self, data: TestimonialDTO) -> TestimonialResponseDTO:
        try:
            logger.info("Creating testimonial from user: %s", data.user_id)
            result = self._repo.create(data)
            logger.info("Testimonial created: id=%s", result.id)
            return result
        except AlreadyExists:
            logger.error("Testimonial already exists from user: %s", data.user_id)
            raise AlreadyExists("Testimonial already exists")
        except DatabaseError:
            logger.error("Database error while creating testimonial")
            raise DatabaseError("Database error while creating testimonial")

    def get_testimonial(self, testimonial_id: str) -> TestimonialResponseDTO:
        try:
            return self._repo.get_by_id(testimonial_id)
        except NotFound:
            logger.error("Testimonial not found: %s", testimonial_id)
            raise NotFound("Testimonial not found")
        except DatabaseError:
            logger.error("Database error while fetching testimonial")
            raise DatabaseError("Database error while fetching testimonial")

    def list_testimonials(self, approved_only: bool = True) -> list[TestimonialResponseDTO]:
        try:
            return self._repo.get_all(approved_only=approved_only)
        except DatabaseError:
            logger.error("Database error while fetching testimonials")
            raise DatabaseError("Database error while fetching testimonials")

    def update_testimonial(self, testimonial_id: str, updates: dict) -> TestimonialResponseDTO:
        try:
            allowed = {"content", "rating", "is_approved", "display_order"}
            safe_updates = {k: v for k, v in updates.items() if k in allowed}
            logger.info("Updating testimonial id=%s fields=%s", testimonial_id, list(safe_updates.keys()))
            result = self._repo.update(testimonial_id, safe_updates)
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
