from __future__ import annotations
from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from tuned.models import Payment, User, Order, AcceptedPaymentMethod
from tuned.models.enums import PaymentStatus
from tuned.dtos.payment import AdminPaymentResponseDTO
from tuned.core.exceptions import DatabaseError
from tuned.core.logging import get_logger

logger = get_logger(__name__)

class GetAdminPaymentsList:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(
        self,
        status: Optional[str] = None,
        q: Optional[str] = None,
        page: int = 1,
        per_page: int = 10
    ) -> tuple[list[AdminPaymentResponseDTO], int]:
        try:
            stmt = (
                select(
                    Payment,
                    func.concat(User.first_name, " ", User.last_name).label("client_name"),
                    User.email.label("client_email"),
                    Order.order_number.label("order_number"),
                    AcceptedPaymentMethod.name.label("method_name"),
                    AcceptedPaymentMethod.category.label("method_category")
                )
                .join(User, Payment.user_id == User.id)
                .join(Order, Payment.order_id == Order.id)
                .join(AcceptedPaymentMethod, Payment.accepted_method_id == AcceptedPaymentMethod.id)
            )

            if status:
                try:
                    stmt = stmt.where(Payment.status == PaymentStatus(status.lower()))
                except ValueError:
                    stmt = stmt.where(Payment.status == PaymentStatus[status.upper()])

            if q:
                search_pattern = f"%{q}%"
                stmt = stmt.where(
                    Payment.payment_id.ilike(search_pattern) |
                    Order.order_number.ilike(search_pattern) |
                    User.first_name.ilike(search_pattern) |
                    User.last_name.ilike(search_pattern) |
                    User.email.ilike(search_pattern)
                )

            count_stmt = select(func.count()).select_from(stmt.subquery())
            total = self.session.scalar(count_stmt) or 0

            stmt = stmt.order_by(Payment.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
            results = self.session.execute(stmt).all()

            payments_list = []
            for payment, client_name, client_email, order_number, method_name, method_category in results:
                payments_list.append(
                    AdminPaymentResponseDTO.from_model_and_relations(
                        model=payment,
                        client_name=client_name or "",
                        client_email=client_email or "",
                        order_number=order_number or "",
                        payment_method_name=method_name or "",
                        payment_method_category=method_category.value if method_category else ""
                    )
                )
            return payments_list, total
        except SQLAlchemyError as exc:
            logger.error("[GetAdminPaymentsList] DB error: %s", exc)
            raise DatabaseError(str(exc)) from exc
        except Exception as exc:
            logger.error("[GetAdminPaymentsList] Unexpected error: %s", exc)
            raise DatabaseError(str(exc)) from exc
