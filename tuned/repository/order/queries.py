from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy import func, desc, asc
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from tuned.models import (
    Order, Payment, Referral, ActivityLog, ServiceCategory,
    OrderDeadlineExtensionRequest,
)
from tuned.models.enums import (
    OrderStatus, PaymentStatus, ActionableAlertType, ExtensionRequestStatus,
)
from tuned.dtos.dashboard import ActionableAlertDTO
from tuned.repository.exceptions import NotFound, DatabaseError
from tuned.core.logging import get_logger

logger: logging.Logger = get_logger(__name__)

_ACTIVE_STATUSES = (OrderStatus.ACTIVE, OrderStatus.REVISION)


class GetActiveOrdersByClient:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, client_id: str) -> list[Order]:
        try:
            return (
                self.db.query(Order)
                .filter(
                    Order.client_id == client_id,
                    Order.status.in_(_ACTIVE_STATUSES),
                )
                .all()
            )
        except SQLAlchemyError as exc:
            logger.error("[GetActiveOrdersByClient] DB error: %s", exc)
            raise DatabaseError(str(exc)) from exc


class GetLatestActiveOrderByClient:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, client_id: str) -> Optional[Order]:
        try:
            return (
                self.db.query(Order)
                .filter(
                    Order.client_id == client_id,
                    Order.status.in_(_ACTIVE_STATUSES),
                )
                .order_by(desc(Order.updated_at))
                .first()
            )
        except SQLAlchemyError as exc:
            logger.error("[GetLatestActiveOrderByClient] DB error: %s", exc)
            raise DatabaseError(str(exc)) from exc


class GetUpcomingDeadlines:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, client_id: str, limit: int = 3) -> list[Order]:
        try:
            return (
                self.db.query(Order)
                .filter(
                    Order.client_id == client_id,
                    Order.status.in_(_ACTIVE_STATUSES),
                    Order.due_date.isnot(None),
                )
                .order_by(asc(Order.due_date))
                .limit(limit)
                .all()
            )
        except SQLAlchemyError as exc:
            logger.error("[GetUpcomingDeadlines] DB error: %s", exc)
            raise DatabaseError(str(exc)) from exc

class GetSpendingVelocity:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _month_label_expr(self, column: object) -> object:
        dialect = self.db.bind.dialect.name
        if dialect == "postgresql":
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
            window: dict[str, float] = {}
            for i in range(months - 1, -1, -1):
                key = (now - timedelta(days=30 * i)).strftime("%Y-%m")
                window[key] = 0.0
            for label, total in rows:
                if label in window:
                    window[label] = float(total or 0.0)
            return list(window.items())
        except SQLAlchemyError as exc:
            logger.error("[GetSpendingVelocity] DB error: %s", exc)
            raise DatabaseError(str(exc)) from exc


class GetProjectLifecycle:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, client_id: str) -> list[tuple[str, int]]:
        try:
            rows = (
                self.db.query(Order.status, func.count(Order.id))
                .filter(Order.client_id == client_id)
                .group_by(Order.status)
                .all()
            )
            return [(status.name, count) for status, count in rows]
        except SQLAlchemyError as exc:
            logger.error("[GetProjectLifecycle] DB error: %s", exc)
            raise DatabaseError(str(exc)) from exc


class GetServiceMix:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, client_id: str) -> list[tuple[str, int]]:
        from tuned.models import Service

        try:
            rows = (
                self.db.query(ServiceCategory.name, func.count(Order.id))
                .join(Service, Order.service_id == Service.id)
                .join(ServiceCategory, Service.category_id == ServiceCategory.id)
                .filter(Order.client_id == client_id)
                .group_by(ServiceCategory.name)
                .all()
            )
            return [(name, count) for name, count in rows]
        except SQLAlchemyError as exc:
            logger.error("[GetServiceMix] DB error: %s", exc)
            raise DatabaseError(str(exc)) from exc


class GetReferralGrowth:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _month_label_expr(self, column: object) -> object:
        dialect = self.db.bind.dialect.name
        if dialect == "postgresql":
            return func.to_char(column, "YYYY-MM")
        return func.strftime("%Y-%m", column)

    def execute(self, referrer_id: str, months: int = 6) -> list[tuple[str, float]]:
        try:
            month_expr = self._month_label_expr(Referral.created_at)
            rows = (
                self.db.query(month_expr, func.sum(Referral.commission))
                .filter(Referral.referrer_id == referrer_id)
                .group_by(month_expr)
                .order_by(asc(month_expr))
                .all()
            )
            now = datetime.now(timezone.utc)
            window: dict[str, float] = {}
            for i in range(months - 1, -1, -1):
                key = (now - timedelta(days=30 * i)).strftime("%Y-%m")
                window[key] = 0.0
            for label, total in rows:
                if label in window:
                    window[label] = float(total or 0.0)
            return list(window.items())
        except SQLAlchemyError as exc:
            logger.error("[GetReferralGrowth] DB error: %s", exc)
            raise DatabaseError(str(exc)) from exc

class GetActivityFeed:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, user_id: str, limit: int = 10) -> list[ActivityLog]:
        try:
            return (
                self.db.query(ActivityLog)
                .filter(ActivityLog.user_id == user_id)
                .order_by(desc(ActivityLog.created_at))
                .limit(limit)
                .all()
            )
        except SQLAlchemyError as exc:
            logger.error("[GetActivityFeed] DB error: %s", exc)
            raise DatabaseError(str(exc)) from exc

class GetActionableAlerts:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, client_id: str) -> list[ActionableAlertDTO]:
        try:
            alerts: list[ActionableAlertDTO] = []

            ext_requests = (
                self.db.query(OrderDeadlineExtensionRequest)
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
                self.db.query(Order)
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


class GetOrderForReorder:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, order_id: str, client_id: str) -> Order:
        try:
            order = (
                self.db.query(Order)
                .filter(
                    Order.id == order_id,
                    Order.client_id == client_id,
                )
                .first()
            )
            if not order:
                raise NotFound(f"Order {order_id} not found for client {client_id}")
            return order
        except NotFound:
            raise
        except SQLAlchemyError as exc:
            logger.error("[GetOrderForReorder] DB error: %s", exc)
            raise DatabaseError(str(exc)) from exc


class CreateOrderFromReorder:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, source: Order, client_id: str) -> Order:
        try:
            new_order = Order(
                client_id=client_id,
                service_id=source.service_id,
                academic_level_id=source.academic_level_id,
                deadline_id=source.deadline_id,
                title=source.title,
                description=source.description,
                word_count=source.word_count,
                page_count=source.page_count,
                format_style=source.format_style,
                report_type=source.report_type,
                total_price=source.total_price,
                price_per_page=source.price_per_page,
                subtotal=source.subtotal,
                discount_amount=source.discount_amount or 0,
                status=OrderStatus.PENDING,
                paid=False,
            )
            self.db.add(new_order)
            self.db.commit()
            self.db.refresh(new_order)
            return new_order
        except SQLAlchemyError as exc:
            self.db.rollback()
            logger.error("[CreateOrderFromReorder] DB error: %s", exc)
            raise DatabaseError(str(exc)) from exc
