from __future__ import annotations
import logging
from typing import Optional, TYPE_CHECKING

from tuned.dtos import AcademicLevelDTO, AcademicLevelResponseDTO, AcademicLevelUpdateDTO
from tuned.repository.exceptions import AlreadyExists, DatabaseError, NotFound
from tuned.core.logging import get_logger

if TYPE_CHECKING:
    from tuned.repository import Repository

logger: logging.Logger = get_logger(__name__)


class AcademicLevelService:
    def __init__(self, repos: Optional[Repository] = None) -> None:
        if repos:
            self._repo = repos.academic_level
        else:
            from tuned.repository import repositories
            self._repo = repositories.academic_level

    def create_academic_level(self, data: AcademicLevelDTO) -> AcademicLevelResponseDTO:
        try:
            logger.info("Creating academic level: %s", data.name)
            result = self._repo.create(data)
            logger.info("Academic level created: id=%s", result.id)
            return result
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

    def update_academic_level(self, level_id: str, updates: AcademicLevelUpdateDTO) -> AcademicLevelResponseDTO:
        try:
            logger.info("Updating academic level id=%s", level_id)
            result = self._repo.update(level_id, updates)
            logger.info("Academic level updated: id=%s", level_id)
            return result
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
