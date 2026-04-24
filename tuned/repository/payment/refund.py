from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from tuned.models import Refund, RefundStatus
from tuned.dtos.payment import RefundCreateDTO, RefundUpdateDTO, RefundResponseDTO
from tuned.repository.exceptions import DatabaseError, AlreadyExists, NotFound
from tuned.core.logging import get_logger

logger = get_logger(__name__)

class CreateRefund:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, data: RefundCreateDTO) -> RefundResponseDTO:
        try:
            refund = Refund(
                payment_id=data.payment_id,
                amount=data.amount,
                reason=data.reason,
                status=getattr(RefundStatus, data.status.upper(), RefundStatus.PENDING) if data.status else RefundStatus.PENDING,
                processed_by=data.processed_by,
                processor_refund_id=data.processor_refund_id,
                refund_date=data.refund_date,
            )
            self.db.add(refund)
            self.db.commit()
            return RefundResponseDTO.from_model(refund)
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"[CreateRefund] Integrity error: {e}")
            raise AlreadyExists("Refund could not be created due to an integrity conflict.") from e
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"[CreateRefund] DB error: {e}")
            raise DatabaseError("Database error while creating refund.") from e

class GetRefundByID:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, refund_id: str) -> RefundResponseDTO:
        try:
            refund = self.db.query(Refund).filter(Refund.id == refund_id).first()
            if not refund:
                raise NotFound("Refund not found.")
            return RefundResponseDTO.from_model(refund)
        except SQLAlchemyError as e:
            logger.error(f"[GetRefundByID] DB error: {e}")
            raise DatabaseError("Database error while fetching refund.") from e

class UpdateRefundStatus:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, refund_id: str, data: RefundUpdateDTO) -> RefundResponseDTO:
        try:
            refund = self.db.query(Refund).filter(Refund.id == refund_id).first()
            if not refund:
                raise NotFound("Refund not found.")
                
            if data.status:
                refund.status = getattr(RefundStatus, data.status.upper(), data.status)
                
            self.db.commit()
            return RefundResponseDTO.from_model(refund)
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"[UpdateRefundStatus] Integrity error: {e}")
            raise DatabaseError("Conflict updating refund.") from e
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"[UpdateRefundStatus] DB error: {e}")
            raise DatabaseError("Database error while updating refund.") from e
