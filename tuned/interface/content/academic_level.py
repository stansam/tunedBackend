import logging
from typing import Optional

from tuned.models import AcademicLevel
from tuned.dtos import AcademicLevelDTO, AcademicLevelResponseDTO
from tuned.repository import repositories
from tuned.repository.exceptions import AlreadyExists, DatabaseError, NotFound

logger = logging.getLogger(__name__)


class AcademicLevelService:
    """Service layer for AcademicLevel business logic."""

    def __init__(self) -> None:
        self._repo = repositories.academic_level

    def create_academic_level(self, data: AcademicLevelDTO) -> AcademicLevelResponseDTO:
        """Create a new academic level.

        Raises:
            AlreadyExists: If an academic level with the same name already exists.
            DatabaseError: On unexpected database failure.
        """
        logger.info("Creating academic level: %s", data.name)
        level = self._repo.create(data)
        logger.info("Academic level created: id=%s name=%s", level.id, level.name)
        return level

    def get_academic_level(self, level_id: str) -> AcademicLevelResponseDTO:
        """Retrieve a single academic level by its ID.

        Raises:
            NotFound: If no academic level exists with the given ID.
            DatabaseError: On unexpected database failure.
        """
        return self._repo.get_by_id(level_id)

    def list_academic_levels(self) -> list[AcademicLevelResponseDTO]:
        """Return all academic levels ordered by their display order.

        Raises:
            DatabaseError: On unexpected database failure.
        """
        return self._repo.get_all()

    def update_academic_level(self, level_id: str, updates: dict) -> AcademicLevelResponseDTO:
        """Update mutable fields of an academic level.

        Only keys present on the model are applied; unknown keys are silently
        ignored to guard against mass-assignment.

        Raises:
            NotFound: If no academic level exists with the given ID.
            AlreadyExists: If the update would create a name conflict.
            DatabaseError: On unexpected database failure.
        """
        allowed_fields = {"name", "order"}
        safe_updates = {k: v for k, v in updates.items() if k in allowed_fields}
        logger.info("Updating academic level id=%s fields=%s", level_id, list(safe_updates.keys()))
        level = self._repo.update(level_id, safe_updates)
        logger.info("Academic level updated: id=%s", level_id)
        return level

    def delete_academic_level(self, level_id: str) -> None:
        """Permanently delete an academic level.

        Raises:
            NotFound: If no academic level exists with the given ID.
            DatabaseError: On unexpected database failure.
        """
        logger.info("Deleting academic level id=%s", level_id)
        self._repo.delete(level_id)
        logger.info("Academic level deleted: id=%s", level_id)
