from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from tuned.extensions import db
from tuned.models import AcademicLevel
from tuned.dtos.content import AcademicLevelDTO
from tuned.repository.exceptions import AlreadyExists, DatabaseError, NotFound


class CreateAcademicLevel:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, data: AcademicLevelDTO) -> AcademicLevel:
        try:
            level = AcademicLevel(name=data.name, order=data.order)
            self.db.session.add(level)
            self.db.session.commit()
            return level
        except IntegrityError:
            self.db.session.rollback()
            raise AlreadyExists("Academic level with this name already exists.")
        except SQLAlchemyError as e:
            self.db.session.rollback()
            raise DatabaseError("Database error while creating academic level.") from e


class GetAcademicLevelByID:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, level_id: str) -> AcademicLevel:
        try:
            level = self.db.session.query(AcademicLevel).filter_by(id=level_id).first()
            if not level:
                raise NotFound("Academic level not found.")
            return level
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching academic level: {str(e)}") from e


class GetAllAcademicLevels:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self) -> list[AcademicLevel]:
        try:
            return (
                self.db.session.query(AcademicLevel)
                .order_by(AcademicLevel.order.asc())
                .all()
            )
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching academic levels: {str(e)}") from e


class UpdateAcademicLevel:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, level_id: str, updates: dict) -> AcademicLevel:
        try:
            level = self.db.session.query(AcademicLevel).filter_by(id=level_id).first()
            if not level:
                raise NotFound("Academic level not found.")
            for key, value in updates.items():
                if hasattr(level, key):
                    setattr(level, key, value)
            self.db.session.commit()
            return level
        except IntegrityError:
            self.db.session.rollback()
            raise AlreadyExists("An academic level with that name already exists.")
        except SQLAlchemyError as e:
            self.db.session.rollback()
            raise DatabaseError("Database error while updating academic level.") from e


class DeleteAcademicLevel:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, level_id: str) -> None:
        try:
            level = self.db.session.query(AcademicLevel).filter_by(id=level_id).first()
            if not level:
                raise NotFound("Academic level not found.")
            self.db.session.delete(level)
            self.db.session.commit()
        except SQLAlchemyError as e:
            self.db.session.rollback()
            raise DatabaseError("Database error while deleting academic level.") from e


class AcademicLevelRepository:
    """Facade that composes all academic-level command objects."""

    def __init__(self) -> None:
        self.db = db

    def create(self, data: AcademicLevelDTO) -> AcademicLevel:
        return CreateAcademicLevel(self.db).execute(data)

    def get_by_id(self, level_id: str) -> AcademicLevel:
        return GetAcademicLevelByID(self.db).execute(level_id)

    def get_all(self) -> list[AcademicLevel]:
        return GetAllAcademicLevels(self.db).execute()

    def update(self, level_id: str, updates: dict) -> AcademicLevel:
        return UpdateAcademicLevel(self.db).execute(level_id, updates)

    def delete(self, level_id: str) -> None:
        return DeleteAcademicLevel(self.db).execute(level_id)
