from typing import Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from tuned.extensions import db
from tuned.models import PriceRate
from tuned.dtos.price import PriceRateDTO, PriceRateResponseDTO, PriceRateLookupDTO
from tuned.repository.exceptions import AlreadyExists, DatabaseError, NotFound


class CreatePriceRate:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, data: PriceRateDTO) -> PriceRateResponseDTO:
        try:
            rate = PriceRate(
                pricing_category_id=data.pricing_category_id,
                academic_level_id=data.academic_level_id,
                deadline_id=data.deadline_id,
                price_per_page=data.price_per_page,
                is_active=data.is_active if data.is_active is not None else True,
            )
            self.session.add(rate)
            self.session.commit()
            return PriceRateResponseDTO.from_model(rate)
        except IntegrityError:
            self.session.rollback()
            raise AlreadyExists(
                "A price rate for this category/academic level/deadline combination already exists."
            )
        except SQLAlchemyError as e:
            self.session.rollback()
            raise DatabaseError("Database error while creating price rate.") from e


class GetPriceRateByID:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, rate_id: str) -> PriceRateResponseDTO:
        try:
            rate = self.session.query(PriceRate).filter_by(id=rate_id).first()
            if not rate:
                raise NotFound("Price rate not found.")
            return PriceRateResponseDTO.from_model(rate)
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching price rate: {str(e)}") from e


class GetPriceRateByDimensions:
    """Look up the unique rate for a given category + level + deadline triple."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, lookup: PriceRateLookupDTO) -> PriceRateResponseDTO:
        try:
            rate = (
                self.session.query(PriceRate)
                .filter_by(
                    pricing_category_id=lookup.pricing_category_id,
                    academic_level_id=lookup.academic_level_id,
                    deadline_id=lookup.deadline_id,
                    is_active=True,
                )
                .first()
            )
            if not rate:
                raise NotFound("No active price rate found for the given combination.")
            return PriceRateResponseDTO.from_model(rate)
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error during rate lookup: {str(e)}") from e


class GetPriceRatesByCategory:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, pricing_category_id: str, active_only: bool = True) -> list[PriceRateResponseDTO]:
        try:
            query = self.session.query(PriceRate).filter_by(
                pricing_category_id=pricing_category_id
            )
            if active_only:
                query = query.filter_by(is_active=True)
            rates = query.all()
            return [PriceRateResponseDTO.from_model(r) for r in rates]
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching price rates: {str(e)}") from e


class UpdatePriceRate:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, rate_id: str, updates: dict[str, Any]) -> PriceRateResponseDTO:
        try:
            rate = self.session.query(PriceRate).filter_by(id=rate_id).first()
            if not rate:
                raise NotFound("Price rate not found.")
            for key, value in updates.items():
                if hasattr(rate, key):
                    setattr(rate, key, value)
            self.session.commit()
            return PriceRateResponseDTO.from_model(rate)
        except IntegrityError:
            self.session.rollback()
            raise AlreadyExists(
                "A price rate for this category/academic level/deadline combination already exists."
            )
        except SQLAlchemyError as e:
            self.session.rollback()
            raise DatabaseError("Database error while updating price rate.") from e


class DeletePriceRate:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, rate_id: str) -> None:
        try:
            rate = self.session.query(PriceRate).filter_by(id=rate_id).first()
            if not rate:
                raise NotFound("Price rate not found.")
            self.session.delete(rate)
            self.session.commit()
        except SQLAlchemyError as e:
            self.session.rollback()
            raise DatabaseError("Database error while deleting price rate.") from e


class PriceRateRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, data: PriceRateDTO) -> PriceRateResponseDTO:
        return CreatePriceRate(self.session).execute(data)

    def get_by_id(self, rate_id: str) -> PriceRateResponseDTO:
        return GetPriceRateByID(self.session).execute(rate_id)

    def get_by_dimensions(self, lookup: PriceRateLookupDTO) -> PriceRateResponseDTO:
        return GetPriceRateByDimensions(self.session).execute(lookup)

    def get_by_category(
        self, pricing_category_id: str, active_only: bool = True
    ) -> list[PriceRateResponseDTO]:
        return GetPriceRatesByCategory(self.session).execute(pricing_category_id, active_only)

    def update(self, rate_id: str, updates: dict[str, Any]) -> PriceRateResponseDTO:
        return UpdatePriceRate(self.session).execute(rate_id, updates)

    def delete(self, rate_id: str) -> None:
        return DeletePriceRate(self.session).execute(rate_id)
