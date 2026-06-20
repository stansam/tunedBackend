from typing import Any, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from tuned.models import Payment, PaymentStatus
from tuned.dtos.payment import PaymentCreateDTO, PaymentUpdateDTO, PaymentResponseDTO
from tuned.repository.exceptions import DatabaseError, AlreadyExists, NotFound
from tuned.core.logging import get_logger
from datetime import datetime, timezone
from flask import current_app
from tuned.repository.utils import build_month_window
from tuned.utils.variables import Variables

logger = get_logger(__name__)

class CreatePayment:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, data: PaymentCreateDTO) -> PaymentResponseDTO:
        try:
            try:
                # TODO: Implement TransactionStatus Enum
                status = PaymentStatus(data.status.lower()) if data.status else PaymentStatus.PENDING
            except ValueError:
                raise ValueError(f"Invalid payment status: {data.status}")
            payment = Payment(
                order_id=UUID(data.order_id),
                user_id=UUID(data.user_id),
                amount=data.amount,
                accepted_method_id=UUID(data.accepted_method_id),
                status=status,
            )
            self.session.add(payment)
            self.session.flush()
            return PaymentResponseDTO.from_model(payment)
        except IntegrityError as e:
            logger.error(f"[CreatePayment] Integrity error: {e}")
            raise AlreadyExists("Payment record could not be created due to an integrity conflict.") from e
        except SQLAlchemyError as e:
            logger.error(f"[CreatePayment] DB error: {e}")
            raise DatabaseError("Database error while creating payment.") from e

class GetPaymentByID:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, payment_id: str) -> Payment:
        try:
            stmt = select(Payment).where(Payment.id == payment_id)
            payment = self.session.scalar(stmt)
            if not payment:
                raise NotFound("Payment not found.")
            return payment
        except SQLAlchemyError as e:
            logger.error(f"[GetPaymentByID] DB error: {e}")
            raise DatabaseError("Database error while fetching payment.") from e

class GetPaymentByOrderID:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, order_id: str) -> list[PaymentResponseDTO]:
        try:
            stmt = select(Payment).where(Payment.order_id == order_id)
            payments = self.session.scalars(stmt).all()
            return [PaymentResponseDTO.from_model(p) for p in payments]
        except SQLAlchemyError as e:
            logger.error(f"[GetPaymentByOrderID] DB error: {e}")
            raise DatabaseError("Database error while fetching payments for order.") from e

class UpdatePayment:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, payment_id: str, data: PaymentUpdateDTO) -> Payment:
        try:
            stmt = select(Payment).where(Payment.id == payment_id)
            payment = self.session.scalar(stmt)
            if not payment:
                raise NotFound("Payment not found.")
                
            if data.status:
                try:
                    payment.status = PaymentStatus(data.status.lower())
                except ValueError:
                    try:
                        payment.status = PaymentStatus[data.status.upper()]
                    except KeyError:
                        raise ValueError(f"Invalid payment status: {data.status}")
            if data.client_proof_reference is not None:
                payment.client_proof_reference = data.client_proof_reference
            if data.client_marked_paid_at is not None:
                payment.client_marked_paid_at = data.client_marked_paid_at
            if data.admin_verified_at is not None:
                payment.admin_verified_at = data.admin_verified_at
                
            self.session.flush()
            return payment
        except IntegrityError as e:
            logger.error(f"[UpdatePayment] Integrity error: {e}")
            raise DatabaseError("Conflict updating payment.") from e
        except SQLAlchemyError as e:
            logger.error(f"[UpdatePayment] DB error: {e}")
            raise DatabaseError("Database error while updating payment.") from e

class GetSpendingVelocity:
    def __init__(self, session: Session) -> None:
        self.session = session

    def _month_label_expr(self, column: Any) -> Any: # TODO: Type Hint the data dict
        # if current_app.config["FLASK_ENV"] == Variables.PRODUCTION:
        return func.to_char(column, "YYYY-MM")
        # return func.strftime("%Y-%m", column)

    def execute(self, client_id: str, months: int = 6) -> list[tuple[str, float]]:
        try:
            month_expr = self._month_label_expr(Payment.created_at)
            stmt = (
                select(month_expr, func.sum(Payment.amount))
                .where(
                    Payment.user_id == client_id,
                    Payment.status == PaymentStatus.COMPLETED,
                )
                .group_by(month_expr)
                .order_by(month_expr.asc())
            )
            rows = self.session.execute(stmt).all()
            
            now = datetime.now(timezone.utc)
            window: dict[str, float] = build_month_window(now, months)
            for label, total in rows:
                if label in window:
                    window[label] = float(total or 0.0)
            return list(window.items())
        except SQLAlchemyError as exc:
            logger.error("[GetSpendingVelocity] DB error: %s", exc)
            raise DatabaseError(str(exc)) from exc

class GetPendingPaymentByOrderID:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, order_id: str, accepted_method_id: str) -> Payment:
        try:
            stmt = select(Payment).where(
                Payment.order_id == order_id,
                Payment.accepted_method_id == accepted_method_id,
                Payment.status == PaymentStatus.PENDING
            )
            payment = self.session.scalar(stmt)
            if not payment:
                raise NotFound("Payment not found.")
            return payment
        except SQLAlchemyError as e:
            logger.error(f"[GetPendingPaymentByOrderID] DB error: {e}")
            raise DatabaseError("Database error while fetching payments for order.") from e

class GetPendingPaymentByReferenceID:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, reference_id: str) -> Payment:
        try:
            stmt = select(Payment).where(
                Payment.client_proof_reference == reference_id,
                Payment.status.in_([PaymentStatus.PENDING, PaymentStatus.PENDING_VERIFICATION])
            )
            payment = self.session.scalar(stmt)
            if not payment:
                raise NotFound("Payment not found.")
            return payment
        except SQLAlchemyError as e:
            logger.error(f"[GetPendingPaymentByReferenceID] DB error: {e}")
            raise DatabaseError("Database error while fetching payments for order.") from e


class GetPaymentsList:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, user_id: Optional[str] = None, status: Optional[str] = None, page: int = 1, per_page: int = 10) -> tuple[list[PaymentResponseDTO], int]:
        try:
            stmt = select(Payment)
            if user_id:
                stmt = stmt.where(Payment.user_id == UUID(user_id))
            if status:
                try:
                    stmt = stmt.where(Payment.status == PaymentStatus(status.lower()))
                except ValueError:
                    try:
                        stmt = stmt.where(Payment.status == PaymentStatus[status.upper()])
                    except KeyError:
                        raise ValueError(f"Invalid payment status filter: {status}")
            
            # Count query
            count_stmt = select(func.count()).select_from(stmt.subquery())
            total = self.session.scalar(count_stmt) or 0
            
            # Pagination & ordering (newest first)
            stmt = stmt.order_by(Payment.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
            payments = self.session.scalars(stmt).all()
            
            return [PaymentResponseDTO.from_model(p) for p in payments], total
        except SQLAlchemyError as e:
            logger.error(f"[GetPaymentsList] DB error: {e}")
            raise DatabaseError("Database error while listing payments.") from e

