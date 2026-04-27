from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from tuned.models import Discount, DiscountType
from tuned.dtos.payment import DiscountCreateDTO, DiscountUpdateDTO, DiscountResponseDTO
from tuned.repository.exceptions import DatabaseError, AlreadyExists, NotFound
from tuned.core.logging import get_logger

logger = get_logger(__name__)

class CreateDiscount:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, data: DiscountCreateDTO) -> DiscountResponseDTO:
        try:
            discount = Discount(
                code=data.code,
                amount=data.amount,
                discount_type=getattr(DiscountType, data.discount_type.upper(), DiscountType.PERCENTAGE) if data.discount_type else DiscountType.PERCENTAGE,
                description=data.description,
                min_order_value=data.min_order_value,
                max_discount_value=data.max_discount_value,
                valid_from=data.valid_from,
                valid_to=data.valid_to,
                usage_limit=data.usage_limit,
                is_active=data.is_active,
            )
            self.session.add(discount)
            self.session.flush()
            return DiscountResponseDTO.from_model(discount)
        except IntegrityError as e:
            logger.error(f"[CreateDiscount] Integrity error: {e}")
            raise AlreadyExists("Discount code already exists.") from e
        except SQLAlchemyError as e:
            logger.error(f"[CreateDiscount] DB error: {e}")
            raise DatabaseError("Database error while creating discount.") from e

class GetDiscountByID:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, discount_id: str) -> DiscountResponseDTO:
        try:
            stmt = select(Discount).where(Discount.id == discount_id)
            discount = self.session.scalar(stmt)
            if not discount:
                raise NotFound("Discount not found.")
            return DiscountResponseDTO.from_model(discount)
        except SQLAlchemyError as e:
            logger.error(f"[GetDiscountByID] DB error: {e}")
            raise DatabaseError("Database error while fetching discount.") from e

class GetDiscountByCode:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, code: str) -> DiscountResponseDTO:
        try:
            stmt = select(Discount).where(Discount.code == code)
            discount = self.session.scalar(stmt)
            if not discount:
                raise NotFound("Discount not found.")
            return DiscountResponseDTO.from_model(discount)
        except SQLAlchemyError as e:
            logger.error(f"[GetDiscountByCode] DB error: {e}")
            raise DatabaseError("Database error while fetching discount.") from e

class UpdateDiscount:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, discount_id: str, data: DiscountUpdateDTO) -> DiscountResponseDTO:
        try:
            stmt = select(Discount).where(Discount.id == discount_id)
            discount = self.session.scalar(stmt)
            if not discount:
                raise NotFound("Discount not found.")
                
            if data.description is not None:
                discount.description = data.description
            if data.is_active is not None:
                discount.is_active = data.is_active
            if data.valid_to is not None:
                discount.valid_to = data.valid_to
                
            self.session.flush()
            return DiscountResponseDTO.from_model(discount)
        except IntegrityError as e:
            logger.error(f"[UpdateDiscount] Integrity error: {e}")
            raise DatabaseError("Conflict updating discount.") from e
        except SQLAlchemyError as e:
            logger.error(f"[UpdateDiscount] DB error: {e}")
            raise DatabaseError("Database error while updating discount.") from e

class IncrementDiscountUsage:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, discount_id: str) -> DiscountResponseDTO:
        try:
            stmt = select(Discount).where(Discount.id == discount_id)
            discount = self.session.scalar(stmt)
            if not discount:
                raise NotFound("Discount not found.")
            
            discount.times_used += 1
            if discount.usage_limit and discount.times_used >= discount.usage_limit:
                discount.is_active = False
                
            self.session.flush()
            return DiscountResponseDTO.from_model(discount)
        except SQLAlchemyError as e:
            logger.error(f"[IncrementDiscountUsage] DB error: {e}")
            raise DatabaseError("Database error while updating discount usage.") from e
