from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from tuned.models import Refund, RefundStatus
from tuned.dtos.payment import RefundCreateDTO, RefundUpdateDTO, RefundResponseDTO
from tuned.repository.exceptions import DatabaseError, AlreadyExists, NotFound
from tuned.core.logging import get_logger

logger = get_logger(__name__)

class CreateRefund:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, data: RefundCreateDTO) -> RefundResponseDTO:
        try:
            try:
                status = RefundStatus(data.status.lower()) if data.status else RefundStatus.PENDING
            except ValueError:
                raise ValueError(f"Invalid refund status: {data.status}")
            refund = Refund(
                payment_id=data.payment_id,
                amount=data.amount,
                reason=data.reason,
                status=status,
                processed_by=data.processed_by,
                admin_reference_id=data.admin_reference_id,
                refund_date=data.refund_date,
            )
            self.session.add(refund)
            self.session.flush()
            return RefundResponseDTO.from_model(refund)
        except IntegrityError as e:
            logger.error(f"[CreateRefund] Integrity error: {e}")
            raise AlreadyExists("Refund could not be created due to an integrity conflict.") from e
        except SQLAlchemyError as e:
            logger.error(f"[CreateRefund] DB error: {e}")
            raise DatabaseError("Database error while creating refund.") from e

class GetRefundByID:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, refund_id: str) -> RefundResponseDTO:
        try:
            stmt = select(Refund).where(Refund.id == refund_id)
            refund = self.session.scalar(stmt)
            if not refund:
                raise NotFound("Refund not found.")
            return RefundResponseDTO.from_model(refund)
        except SQLAlchemyError as e:
            logger.error(f"[GetRefundByID] DB error: {e}")
            raise DatabaseError("Database error while fetching refund.") from e

class UpdateRefundStatus:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, refund_id: str, data: RefundUpdateDTO) -> RefundResponseDTO:
        try:
            stmt = select(Refund).where(Refund.id == refund_id)
            refund = self.session.scalar(stmt)
            if not refund:
                raise NotFound("Refund not found.")
                
            if data.status:
                try:
                    refund.status = RefundStatus(data.status.lower())
                except ValueError:
                    try:
                        refund.status = RefundStatus[data.status.upper()]
                    except KeyError:
                        raise ValueError(f"Invalid refund status: {data.status}")
                
            self.session.flush()
            return RefundResponseDTO.from_model(refund)
        except IntegrityError as e:
            logger.error(f"[UpdateRefundStatus] Integrity error: {e}")
            raise DatabaseError("Conflict updating refund.") from e
        except SQLAlchemyError as e:
            logger.error(f"[UpdateRefundStatus] DB error: {e}")
            raise DatabaseError("Database error while updating refund.") from e
