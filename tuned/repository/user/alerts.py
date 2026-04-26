import logging
from sqlalchemy.orm import Session
from sqlalchemy import desc
from sqlalchemy.exc import SQLAlchemyError
from tuned.models import Order, OrderDeadlineExtensionRequest
from tuned.models.enums import OrderStatus, ExtensionRequestStatus, ActionableAlertType
from tuned.dtos import ActionableAlertDTO
from tuned.repository.exceptions import DatabaseError
from tuned.core.logging import get_logger


logger: logging.Logger = get_logger(__name__)

class GetActionableAlerts:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, client_id: str) -> list[ActionableAlertDTO]:
        try:
            alerts: list[ActionableAlertDTO] = []

            ext_requests = (
                self.session.query(OrderDeadlineExtensionRequest)
                .join(Order, OrderDeadlineExtensionRequest.order_id == Order.id)
                .filter(
                    Order.client_id == client_id,
                    OrderDeadlineExtensionRequest.status == ExtensionRequestStatus.PENDING,
                )
                .order_by(desc(OrderDeadlineExtensionRequest.requested_at))
                .all()
            )
            for req in ext_requests:
                order_num = req.order.order_number if req.order else "Unknown"
                alerts.append(ActionableAlertDTO(
                    id=str(req.id),
                    type=ActionableAlertType.EXTENSION_REQUEST.value,
                    message=(
                        f"Admin has requested a deadline extension on order "
                        f"{order_num}. Please review and respond."
                    ),
                    metadata={
                        "order_id": str(req.order_id),
                        "extension_request_id": str(req.id),
                    },
                    created_at=req.requested_at.isoformat(),
                ))

            pending_review_orders = (
                self.session.query(Order)
                .filter(
                    Order.client_id == client_id,
                    Order.status == OrderStatus.COMPLETED_PENDING_REVIEW,
                )
                .order_by(desc(Order.updated_at))
                .all()
            )
            for order in pending_review_orders:
                alerts.append(ActionableAlertDTO(
                    id=f"review_{order.id}",
                    type=ActionableAlertType.PENDING_REVIEW.value,
                    message=(
                        f"Order {order.order_number} is awaiting your review. "
                        f"Please approve or request a revision."
                    ),
                    metadata={"order_id": str(order.id)},
                    created_at=(
                        order.updated_at.isoformat()
                        if order.updated_at else order.created_at.isoformat()
                    ),
                ))

            alerts.sort(key=lambda a: a.created_at, reverse=True)
            return alerts

        except SQLAlchemyError as exc:
            logger.error("[GetActionableAlerts] DB error: %s", exc)
            raise DatabaseError(str(exc)) from exc
