import logging
from tuned.dtos import AcademicLevelDTO, AcademicLevelResponseDTO
from tuned.repository import repositories
from tuned.repository.exceptions import AlreadyExists, DatabaseError, NotFound
from tuned.core.logging import get_logger

logger: logging.Logger = get_logger(__name__)


class AcademicLevelService:
    """Service layer for AcademicLevel business logic."""

    def __init__(self) -> None:
        self._repo = repositories.academic_level

    def create_academic_level(self, data: AcademicLevelDTO) -> AcademicLevelResponseDTO:
        try:
            logger.info("Creating academic level: %s", data.name)
            level = self._repo.create(data)
            logger.info("Academic level created: id=%s name=%s", level.id, level.name)
            return level
        except AlreadyExists:
            logger.error("Academic level already exists: %s", data.name)
            raise AlreadyExists("Academic level already exists")
        except DatabaseError:
            logger.error("Database error while creating academic level")
            raise DatabaseError("Database error while creating academic level")

    def get_academic_level(self, level_id: str) -> AcademicLevelResponseDTO:
        try:
            return self._repo.get_by_id(level_id)
        except NotFound:
            logger.error("Academic level not found: %s", level_id)
            raise NotFound("Academic level not found")
        except DatabaseError:
            logger.error("Database error while fetching academic level")
            raise DatabaseError("Database error while fetching academic level")

    def list_academic_levels(self) -> list[AcademicLevelResponseDTO]:
        try:
            return self._repo.get_all()
        except DatabaseError:
            logger.error("Database error while fetching academic levels")
            raise DatabaseError("Database error while fetching academic levels")

    def update_academic_level(self, level_id: str, updates: dict) -> AcademicLevelResponseDTO:
        try:
            allowed_fields = {"name", "order"}
            safe_updates = {k: v for k, v in updates.items() if k in allowed_fields}
            logger.info("Updating academic level id=%s fields=%s", level_id, list(safe_updates.keys()))
            level = self._repo.update(level_id, safe_updates)
            logger.info("Academic level updated: id=%s", level_id)
            return level
        except NotFound:
            logger.error("Academic level not found: %s", level_id)
            raise NotFound("Academic level not found")
        except DatabaseError:
            logger.error("Database error while updating academic level")
            raise DatabaseError("Database error while updating academic level")

    def delete_academic_level(self, level_id: str) -> None:
        try:
            logger.info("Deleting academic level id=%s", level_id)
            self._repo.delete(level_id)
            logger.info("Academic level deleted: id=%s", level_id)
        except NotFound:
            logger.error("Academic level not found: %s", level_id)
            raise NotFound("Academic level not found")
        except DatabaseError:
            logger.error("Database error while deleting academic level")
            raise DatabaseError("Database error while deleting academic level")
