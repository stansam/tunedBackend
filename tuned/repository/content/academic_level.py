from typing import Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from tuned.models import AcademicLevel
from tuned.dtos.content import AcademicLevelDTO, AcademicLevelResponseDTO
from tuned.repository.exceptions import AlreadyExists, DatabaseError, NotFound


class CreateAcademicLevel:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, data: AcademicLevelDTO) -> AcademicLevelResponseDTO:
        try:
            level = AcademicLevel(name=data.name, order=data.order)
            self.session.add(level)
            self.session.commit()
            return AcademicLevelResponseDTO.from_model(level)
        except IntegrityError:
            self.session.rollback()
            raise AlreadyExists("Academic level with this name already exists.")
        except SQLAlchemyError as e:
            self.session.rollback()
            raise DatabaseError("Database error while creating academic level.") from e


class GetAcademicLevelByID:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, level_id: str) -> AcademicLevelResponseDTO:
        try:
            level = self.session.query(AcademicLevel).filter_by(id=level_id).first()
            if not level:
                raise NotFound("Academic level not found.")
            return AcademicLevelResponseDTO.from_model(level)
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching academic level: {str(e)}") from e


class GetAllAcademicLevels:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self) -> list[AcademicLevelResponseDTO]:
        try:
            level = (
                self.session.query(AcademicLevel)
                .order_by(AcademicLevel.order.asc())
                .all()
            )
            return [AcademicLevelResponseDTO.from_model(l) for l in level]
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching academic levels: {str(e)}") from e


class UpdateAcademicLevel:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, level_id: str, updates: dict[str, Any]) -> AcademicLevelResponseDTO: # TODO: Type Hint the data dict
        try:
            level = self.session.query(AcademicLevel).filter_by(id=level_id).first()
            if not level:
                raise NotFound("Academic level not found.")
            for key, value in updates.items():
                if hasattr(level, key):
                    setattr(level, key, value)
            self.session.commit()
            return AcademicLevelResponseDTO.from_model(level)
        except IntegrityError:
            self.session.rollback()
            raise AlreadyExists("An academic level with that name already exists.")
        except SQLAlchemyError as e:
            self.session.rollback()
            raise DatabaseError("Database error while updating academic level.") from e


class DeleteAcademicLevel:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, level_id: str) -> None:
        try:
            level = self.session.query(AcademicLevel).filter_by(id=level_id).first()
            if not level:
                raise NotFound("Academic level not found.")
            self.session.delete(level)
            self.session.commit()
        except SQLAlchemyError as e:
            self.session.rollback()
            raise DatabaseError("Database error while deleting academic level.") from e


class AcademicLevelRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, data: AcademicLevelDTO) -> AcademicLevelResponseDTO:
        return CreateAcademicLevel(self.session).execute(data)

    def get_by_id(self, level_id: str) -> AcademicLevelResponseDTO:
        return GetAcademicLevelByID(self.session).execute(level_id)

    def get_all(self) -> list[AcademicLevelResponseDTO]:
        return GetAllAcademicLevels(self.session).execute()

    def update(self, level_id: str, updates: dict[str, Any]) -> AcademicLevelResponseDTO: # TODO: Type Hint the data dict
        return UpdateAcademicLevel(self.session).execute(level_id, updates)

    def delete(self, level_id: str) -> None:
        return DeleteAcademicLevel(self.session).execute(level_id)
