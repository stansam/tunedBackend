from __future__ import annotations
import logging
from typing import Optional, TYPE_CHECKING

from tuned.dtos import SampleDTO, SampleResponseDTO
from tuned.repository.exceptions import AlreadyExists, DatabaseError, NotFound
from tuned.core.logging import get_logger

if TYPE_CHECKING:
    from tuned.repository import Repository

logger: logging.Logger = get_logger(__name__)


class SampleService:
    """Service layer for academic sample business logic."""

    def __init__(self, repos: Optional[Repository] = None) -> None:
        if repos:
            self._repo = repos.sample
        else:
            from tuned.repository import repositories
            self._repo = repositories.sample

    def create_sample(self, data: SampleDTO) -> SampleResponseDTO:
        try:
            logger.info("Creating academic sample: %s", data.title)
            result = self._repo.create(data)
            logger.info("Academic sample created: id=%s", result.id)
            return result
        except AlreadyExists:
            logger.error("Academic sample already exists: %s", data.title)
            raise AlreadyExists("Academic sample already exists")
        except DatabaseError:
            logger.error("Database error while creating academic sample")
            raise DatabaseError("Database error while creating academic sample")

    def get_sample(self, sample_id: str) -> SampleResponseDTO:
        try:
            return self._repo.get_by_id(sample_id)
        except NotFound:
            logger.error("Academic sample not found: %s", sample_id)
            raise NotFound("Academic sample not found")
        except DatabaseError:
            logger.error("Database error while fetching academic sample")
            raise DatabaseError("Database error while fetching academic sample")

    def list_samples(self, category_id: str | None = None) -> list[SampleResponseDTO]:
        try:
            if category_id:
                return self._repo.get_by_category(category_id)
            return self._repo.get_all()
        except DatabaseError:
            logger.error("Database error while fetching academic samples")
            raise DatabaseError("Database error while fetching academic samples")

    def update_sample(self, sample_id: str, updates: dict) -> SampleResponseDTO:
        try:
            allowed = {"title", "description", "file_url", "service_category_id", "is_active"}
            safe_updates = {k: v for k, v in updates.items() if k in allowed}
            logger.info("Updating academic sample id=%s fields=%s", sample_id, list(safe_updates.keys()))
            result = self._repo.update(sample_id, safe_updates)
            logger.info("Academic sample updated: id=%s", sample_id)
            return result
        except NotFound:
            logger.error("Academic sample not found: %s", sample_id)
            raise NotFound("Academic sample not found")
        except DatabaseError:
            logger.error("Database error while updating academic sample")
            raise DatabaseError("Database error while updating academic sample")

    def delete_sample(self, sample_id: str) -> None:
        try:
            logger.info("Deleting academic sample id=%s", sample_id)
            self._repo.delete(sample_id)
            logger.info("Academic sample deleted: id=%s", sample_id)
        except NotFound:
            logger.error("Academic sample not found: %s", sample_id)
            raise NotFound("Academic sample not found")
        except DatabaseError:
            logger.error("Database error while deleting academic sample")
            raise DatabaseError("Database error while deleting academic sample")
