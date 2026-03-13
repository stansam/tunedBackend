import logging

from tuned.models import Deadline
from tuned.dtos.content import DeadlineDTO
from tuned.repository.content.deadline import DeadlineRepository
from tuned.repository.exceptions import AlreadyExists, DatabaseError, NotFound

logger = logging.getLogger(__name__)


class DeadlineService:
    """Service layer for Deadline business logic."""

    def __init__(self) -> None:
        self._repo = DeadlineRepository()

    def create_deadline(self, data: DeadlineDTO) -> Deadline:
        """Create a new deadline option.

        Raises:
            AlreadyExists: If a deadline with the same name already exists.
            DatabaseError: On unexpected database failure.
        """
        logger.info("Creating deadline: %s (%dh)", data.name, data.hours)
        deadline = self._repo.create(data)
        logger.info("Deadline created: id=%s name=%s", deadline.id, deadline.name)
        return deadline

    def get_deadline(self, deadline_id: str) -> Deadline:
        """Retrieve a single deadline by its ID.

        Raises:
            NotFound: If no deadline exists with the given ID.
            DatabaseError: On unexpected database failure.
        """
        return self._repo.get_by_id(deadline_id)

    def list_deadlines(self) -> list[Deadline]:
        """Return all deadlines ordered by display order then hours.

        Raises:
            DatabaseError: On unexpected database failure.
        """
        return self._repo.get_all()

    def update_deadline(self, deadline_id: str, updates: dict) -> Deadline:
        """Update mutable fields of a deadline.

        Only whitelisted fields are applied to guard against mass-assignment.

        Raises:
            NotFound: If no deadline exists with the given ID.
            AlreadyExists: If the update would create a name conflict.
            DatabaseError: On unexpected database failure.
        """
        allowed_fields = {"name", "hours", "order"}
        safe_updates = {k: v for k, v in updates.items() if k in allowed_fields}
        logger.info("Updating deadline id=%s fields=%s", deadline_id, list(safe_updates.keys()))
        deadline = self._repo.update(deadline_id, safe_updates)
        logger.info("Deadline updated: id=%s", deadline_id)
        return deadline

    def delete_deadline(self, deadline_id: str) -> None:
        """Permanently delete a deadline.

        Raises:
            NotFound: If no deadline exists with the given ID.
            DatabaseError: On unexpected database failure.
        """
        logger.info("Deleting deadline id=%s", deadline_id)
        self._repo.delete(deadline_id)
        logger.info("Deadline deleted: id=%s", deadline_id)
