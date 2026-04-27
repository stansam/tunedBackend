from typing import Any
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from tuned.models import Deadline
from tuned.dtos.content import DeadlineDTO, DeadlineResponseDTO
from tuned.repository.exceptions import AlreadyExists, DatabaseError, NotFound


class CreateDeadline:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, data: DeadlineDTO) -> DeadlineResponseDTO:
        try:
            deadline = Deadline(name=data.name, hours=data.hours, order=data.order)
            self.session.add(deadline)
            self.session.flush()
            return DeadlineResponseDTO.from_model(deadline)
        except IntegrityError:
            raise AlreadyExists("A deadline with this name already exists.")
        except SQLAlchemyError as e:
            raise DatabaseError("Database error while creating deadline.") from e


class GetDeadlineByID:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, deadline_id: str) -> DeadlineResponseDTO:
        try:
            stmt = select(Deadline).where(Deadline.id == deadline_id)
            deadline = self.session.scalar(stmt)
            if not deadline:
                raise NotFound("Deadline not found.")
            return DeadlineResponseDTO.from_model(deadline)
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching deadline: {str(e)}") from e


class GetAllDeadlines:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self) -> list[DeadlineResponseDTO]:
        try:
            stmt = select(Deadline).order_by(Deadline.order.asc(), Deadline.hours.asc())
            deadlines = self.session.scalars(stmt).all()
            return [DeadlineResponseDTO.from_model(d) for d in deadlines]
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching deadlines: {str(e)}") from e


class UpdateDeadline:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, deadline_id: str, updates: dict[str, Any]) -> DeadlineResponseDTO:
        try:
            stmt = select(Deadline).where(Deadline.id == deadline_id)
            deadline = self.session.scalar(stmt)
            if not deadline:
                raise NotFound("Deadline not found.")
            for key, value in updates.items():
                if hasattr(deadline, key):
                    setattr(deadline, key, value)
            self.session.flush()
            return DeadlineResponseDTO.from_model(deadline)
        except IntegrityError:
            raise AlreadyExists("A deadline with that name already exists.")
        except SQLAlchemyError as e:
            raise DatabaseError("Database error while updating deadline.") from e


class DeleteDeadline:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, deadline_id: str) -> None:
        try:
            stmt = select(Deadline).where(Deadline.id == deadline_id)
            deadline = self.session.scalar(stmt)
            if not deadline:
                raise NotFound("Deadline not found.")
            self.session.delete(deadline)
            self.session.flush()
        except SQLAlchemyError as e:
            raise DatabaseError("Database error while deleting deadline.") from e


class DeadlineRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, data: DeadlineDTO) -> DeadlineResponseDTO:
        return CreateDeadline(self.session).execute(data)

    def get_by_id(self, deadline_id: str) -> DeadlineResponseDTO:
        return GetDeadlineByID(self.session).execute(deadline_id)

    def get_all(self) -> list[DeadlineResponseDTO]:
        return GetAllDeadlines(self.session).execute()

    def update(self, deadline_id: str, updates: dict[str, Any]) -> DeadlineResponseDTO:
        return UpdateDeadline(self.session).execute(deadline_id, updates)

    def delete(self, deadline_id: str) -> None:
        return DeleteDeadline(self.session).execute(deadline_id)
