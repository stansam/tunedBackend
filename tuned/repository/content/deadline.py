from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from tuned.extensions import db
from tuned.models import Deadline
from tuned.dtos.content import DeadlineDTO, DeadlineResponseDTO
from tuned.repository.exceptions import AlreadyExists, DatabaseError, NotFound


class CreateDeadline:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, data: DeadlineDTO) -> DeadlineResponseDTO:
        try:
            deadline = Deadline(name=data.name, hours=data.hours, order=data.order)
            self.db.session.add(deadline)
            self.db.session.commit()
            return DeadlineResponseDTO.from_model(deadline)
        except IntegrityError:
            self.db.session.rollback()
            raise AlreadyExists("A deadline with this name already exists.")
        except SQLAlchemyError as e:
            self.db.session.rollback()
            raise DatabaseError("Database error while creating deadline.") from e


class GetDeadlineByID:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, deadline_id: str) -> DeadlineResponseDTO:
        try:
            deadline = self.db.session.query(Deadline).filter_by(id=deadline_id).first()
            if not deadline:
                raise NotFound("Deadline not found.")
            return DeadlineResponseDTO.from_model(deadline)
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching deadline: {str(e)}") from e


class GetAllDeadlines:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self) -> list[DeadlineResponseDTO]:
        try:
            deadline = (
                self.db.session.query(Deadline)
                .order_by(Deadline.order.asc(), Deadline.hours.asc())
                .all()
            )
            return [DeadlineResponseDTO.from_model(d) for d in deadline]
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching deadlines: {str(e)}") from e


class UpdateDeadline:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, deadline_id: str, updates: dict) -> DeadlineResponseDTO:
        try:
            deadline = self.db.session.query(Deadline).filter_by(id=deadline_id).first()
            if not deadline:
                raise NotFound("Deadline not found.")
            for key, value in updates.items():
                if hasattr(deadline, key):
                    setattr(deadline, key, value)
            self.db.session.commit()
            return DeadlineResponseDTO.from_model(deadline)
        except IntegrityError:
            self.db.session.rollback()
            raise AlreadyExists("A deadline with that name already exists.")
        except SQLAlchemyError as e:
            self.db.session.rollback()
            raise DatabaseError("Database error while updating deadline.") from e


class DeleteDeadline:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, deadline_id: str) -> None:
        try:
            deadline = self.db.session.query(Deadline).filter_by(id=deadline_id).first()
            if not deadline:
                raise NotFound("Deadline not found.")
            self.db.session.delete(deadline)
            self.db.session.commit()
        except SQLAlchemyError as e:
            self.db.session.rollback()
            raise DatabaseError("Database error while deleting deadline.") from e


class DeadlineRepository:
    def __init__(self) -> None:
        self.db = db

    def create(self, data: DeadlineDTO) -> DeadlineResponseDTO:
        return CreateDeadline(self.db).execute(data)

    def get_by_id(self, deadline_id: str) -> DeadlineResponseDTO:
        return GetDeadlineByID(self.db).execute(deadline_id)

    def get_all(self) -> list[DeadlineResponseDTO]:
        return GetAllDeadlines(self.db).execute()

    def update(self, deadline_id: str, updates: dict) -> DeadlineResponseDTO:
        return UpdateDeadline(self.db).execute(deadline_id, updates)

    def delete(self, deadline_id: str) -> None:
        return DeleteDeadline(self.db).execute(deadline_id)
