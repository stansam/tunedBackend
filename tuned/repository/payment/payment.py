from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy import func, asc
from tuned.models import Payment, PaymentStatus, MethodCategory, Currency
from tuned.dtos.payment import PaymentCreateDTO, PaymentUpdateDTO, PaymentResponseDTO
from tuned.repository.exceptions import DatabaseError, AlreadyExists, NotFound
from tuned.core.logging import get_logger
from datetime import datetime, timezone
from flask import current_app
from tuned.repository.utils import build_month_window
from tuned.utils.variables import Variables

logger = get_logger(__name__)

class CreatePayment:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, data: PaymentCreateDTO) -> PaymentResponseDTO:
        try:
            try:
                # TODO: Implement TransactionStatus Enum
                status = PaymentStatus(data.status.lower()) if data.status else PaymentStatus.PENDING
            except ValueError:
                raise ValueError(f"Invalid payment status: {data.status}")
            payment = Payment(
                order_id=data.order_id,
                user_id=data.user_id,
                amount=data.amount,
                accepted_method_id=data.accepted_method_id,
                status=status,
            )
            self.db.add(payment)
            self.db.commit()
            return PaymentResponseDTO.from_model(payment)
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"[CreatePayment] Integrity error: {e}")
            raise AlreadyExists("Payment record could not be created due to an integrity conflict.") from e
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"[CreatePayment] DB error: {e}")
            raise DatabaseError("Database error while creating payment.") from e

class GetPaymentByID:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, payment_id: str) -> PaymentResponseDTO:
        try:
            payment = self.db.query(Payment).filter(Payment.id == payment_id).first()
            if not payment:
                raise NotFound("Payment not found.")
            return PaymentResponseDTO.from_model(payment)
        except SQLAlchemyError as e:
            logger.error(f"[GetPaymentByID] DB error: {e}")
            raise DatabaseError("Database error while fetching payment.") from e

class GetPaymentByOrderID:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, order_id: str) -> list[PaymentResponseDTO]:
        try:
            payments = self.db.query(Payment).filter(Payment.order_id == order_id).all()
            return [PaymentResponseDTO.from_model(p) for p in payments]
        except SQLAlchemyError as e:
            logger.error(f"[GetPaymentByOrderID] DB error: {e}")
            raise DatabaseError("Database error while fetching payments for order.") from e

class UpdatePayment:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, payment_id: str, data: PaymentUpdateDTO) -> PaymentResponseDTO:
        try:
            payment = self.db.query(Payment).filter(Payment.id == payment_id).first()
            if not payment:
                raise NotFound("Payment not found.")
                
            if data.status:
                payment.status = getattr(PaymentStatus, data.status.upper(), data.status)
            if data.client_proof_reference is not None:
                payment.client_proof_reference = data.client_proof_reference
            if data.client_marked_paid_at is not None:
                payment.client_marked_paid_at = data.client_marked_paid_at
            if data.admin_verified_at is not None:
                payment.admin_verified_at = data.admin_verified_at
                
            self.db.commit()
            return PaymentResponseDTO.from_model(payment)
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"[UpdatePayment] Integrity error: {e}")
            raise DatabaseError("Conflict updating payment.") from e
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"[UpdatePayment] DB error: {e}")
            raise DatabaseError("Database error while updating payment.") from e

class GetSpendingVelocity:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _month_label_expr(self, column: object) -> object:
        if current_app.config["FLASK_ENV"] == Variables.PRODUCTION:
            return func.to_char(column, "YYYY-MM")
        return func.strftime("%Y-%m", column)

    def execute(self, client_id: str, months: int = 6) -> list[tuple[str, float]]:
        try:
            month_expr = self._month_label_expr(Payment.created_at)
            rows = (
                self.db.query(month_expr, func.sum(Payment.amount))
                .filter(
                    Payment.user_id == client_id,
                    Payment.status == PaymentStatus.COMPLETED,
                )
                .group_by(month_expr)
                .order_by(asc(month_expr))
                .all()
            )
            now = datetime.now(timezone.utc)
            window: dict[str, float] = build_month_window(now, months)
            for label, total in rows:
                if label in window:
                    window[label] = float(total or 0.0)
            return list(window.items())
        except SQLAlchemyError as exc:
            logger.error("[GetSpendingVelocity] DB error: %s", exc)
            raise DatabaseError(str(exc)) from exc