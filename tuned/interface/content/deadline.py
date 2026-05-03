from __future__ import annotations
import logging
from typing import Optional, TYPE_CHECKING

from tuned.dtos import DeadlineDTO, DeadlineResponseDTO, DeadlineUpdateDTO
from tuned.repository.exceptions import AlreadyExists, DatabaseError, NotFound
from tuned.core.logging import get_logger

if TYPE_CHECKING:
    from tuned.repository import Repository

logger: logging.Logger = get_logger(__name__)


class DeadlineService:
    def __init__(self, repos: Repository) -> None:
        self._repo = repos.deadline

    def create_deadline(self, data: DeadlineDTO) -> DeadlineResponseDTO:
        try:
            logger.info("Creating deadline: %s (%d hours)", data.name, data.hours)
            result = self._repo.create(data)
            logger.info("Deadline created: id=%s", result.id)
            return result
        except AlreadyExists:
            logger.error("Deadline already exists: %s", data.name)
            raise AlreadyExists("Deadline already exists")
        except DatabaseError:
            logger.error("Database error while creating deadline")
            raise DatabaseError("Database error while creating deadline")

    def get_deadline(self, deadline_id: str) -> DeadlineResponseDTO:
        try:
            return self._repo.get_by_id(deadline_id)
        except NotFound:
            logger.error("Deadline not found: %s", deadline_id)
            raise NotFound("Deadline not found")
        except DatabaseError:
            logger.error("Database error while fetching deadline")
            raise DatabaseError("Database error while fetching deadline")

    def list_deadlines(self) -> list[DeadlineResponseDTO]:
        try:
            return self._repo.get_all()
        except DatabaseError:
            logger.error("Database error while fetching deadlines")
            raise DatabaseError("Database error while fetching deadlines")

    def update_deadline(self, deadline_id: str, updates: DeadlineUpdateDTO) -> DeadlineResponseDTO:
        try:
            logger.info("Updating deadline id=%s", deadline_id)
            result = self._repo.update(deadline_id, updates)
            logger.info("Deadline updated: id=%s", deadline_id)
            return result
        except NotFound:
            logger.error("Deadline not found: %s", deadline_id)
            raise NotFound("Deadline not found")
        except DatabaseError:
            logger.error("Database error while updating deadline")
            raise DatabaseError("Database error while updating deadline")

    def delete_deadline(self, deadline_id: str) -> None:
        try:
            logger.info("Deleting deadline id=%s", deadline_id)
            self._repo.delete(deadline_id)
            logger.info("Deadline deleted: id=%s", deadline_id)
        except NotFound:
            logger.error("Deadline not found: %s", deadline_id)
            raise NotFound("Deadline not found")
        except DatabaseError:
            logger.error("Database error while deleting deadline")
            raise DatabaseError("Database error while deleting deadline")
