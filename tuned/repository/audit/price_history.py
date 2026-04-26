from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from tuned.models import PriceHistory
from tuned.dtos import PriceHistoryCreateDTO, PriceHistoryResponseDTO
from tuned.repository.exceptions import DatabaseError, NotFound

class CreatePriceHistory:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, data: PriceHistoryCreateDTO) -> PriceHistoryResponseDTO:
        try:
            history = PriceHistory(
                price_rate_id=data.price_rate_id,
                old_price=data.old_price,
                new_price=data.new_price,
                reason=data.reason,
                created_by=data.created_by
            )
            self.session.add(history)
            self.session.commit()
            self.session.refresh(history)
            return PriceHistoryResponseDTO.from_model(history)
        except SQLAlchemyError as e:
            self.session.rollback()
            raise DatabaseError(f"Database error while creating price history: {str(e)}") from e

class GetPriceHistoryByID:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, history_id: str) -> PriceHistoryResponseDTO:
        try:
            history = self.session.query(PriceHistory).filter_by(id=history_id).first()
            if not history:
                raise NotFound("Price history record not found.")
            return PriceHistoryResponseDTO.from_model(history)
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching price history: {str(e)}") from e

class GetPriceHistoryByRate:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, rate_id: str, page: int = 1, per_page: int = 20) -> tuple[list[PriceHistoryResponseDTO], int]:
        try:
            query = self.session.query(PriceHistory).filter_by(price_rate_id=rate_id).order_by(PriceHistory.created_at.desc())
            total = query.count()
            items = query.offset((page - 1) * per_page).limit(per_page).all()
            return [PriceHistoryResponseDTO.from_model(i) for i in items], total
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching history for price rate: {str(e)}") from e

class PriceHistoryRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, data: PriceHistoryCreateDTO) -> PriceHistoryResponseDTO:
        return CreatePriceHistory(self.session).execute(data)

    def get_by_id(self, history_id: str) -> PriceHistoryResponseDTO:
        return GetPriceHistoryByID(self.session).execute(history_id)

    def get_by_rate(self, rate_id: str, page: int = 1, per_page: int = 20) -> tuple[list[PriceHistoryResponseDTO], int]:
        return GetPriceHistoryByRate(self.session).execute(rate_id, page, per_page)
