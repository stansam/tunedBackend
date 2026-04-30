from typing import Any
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from tuned.models import PriceRate
from tuned.dtos.price import PriceRateDTO, PriceRateResponseDTO, PriceRateLookupDTO, PriceRateUpdateDTO
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
            self.session.flush()
            return PriceRateResponseDTO.from_model(rate)
        except IntegrityError:
            raise AlreadyExists(
                "A price rate for this category/academic level/deadline combination already exists."
            )
        except SQLAlchemyError as e:
            raise DatabaseError("Database error while creating price rate.") from e


class GetPriceRateByID:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, rate_id: str) -> PriceRateResponseDTO:
        try:
            stmt = select(PriceRate).where(PriceRate.id == rate_id)
            rate = self.session.scalar(stmt)
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
            stmt = select(PriceRate).where(
                PriceRate.pricing_category_id == lookup.pricing_category_id,
                PriceRate.academic_level_id == lookup.academic_level_id,
                PriceRate.deadline_id == lookup.deadline_id,
                PriceRate.is_active == True,
            )
            rate = self.session.scalar(stmt)
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
            stmt = select(PriceRate).where(
                PriceRate.pricing_category_id == pricing_category_id
            )
            if active_only:
                stmt = stmt.where(PriceRate.is_active == True)
            rates = self.session.scalars(stmt).all()
            return [PriceRateResponseDTO.from_model(r) for r in rates]
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching price rates: {str(e)}") from e


class UpdatePriceRate:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, rate_id: str, updates: PriceRateUpdateDTO) -> PriceRateResponseDTO:
        try:
            stmt = select(PriceRate).where(PriceRate.id == rate_id)
            rate = self.session.scalar(stmt)
            if not rate:
                raise NotFound("Price rate not found.")
            update_data = {k: v for k, v in updates.__dict__.items() if v is not None}
            for key, value in update_data.items():
                if hasattr(rate, key):
                    setattr(rate, key, value)
            self.session.flush()
            return PriceRateResponseDTO.from_model(rate)
        except IntegrityError:
            raise AlreadyExists(
                "A price rate for this category/academic level/deadline combination already exists."
            )
        except SQLAlchemyError as e:
            raise DatabaseError("Database error while updating price rate.") from e


class DeletePriceRate:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, rate_id: str) -> None:
        try:
            stmt = select(PriceRate).where(PriceRate.id == rate_id)
            rate = self.session.scalar(stmt)
            if not rate:
                raise NotFound("Price rate not found.")
            self.session.delete(rate)
            self.session.flush()
        except SQLAlchemyError as e:
            raise DatabaseError("Database error while deleting price rate.") from e


from tuned.repository.protocols import PriceRateRepositoryProtocol

class PriceRateRepository(PriceRateRepositoryProtocol):
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

    def update(self, rate_id: str, updates: PriceRateUpdateDTO) -> PriceRateResponseDTO:
        return UpdatePriceRate(self.session).execute(rate_id, updates)

    def delete(self, rate_id: str) -> None:
        return DeletePriceRate(self.session).execute(rate_id)
