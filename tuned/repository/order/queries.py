from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from tuned.models import Order
from tuned.models.enums import OrderStatus
from tuned.repository.exceptions import NotFound, DatabaseError
from tuned.core.logging import get_logger

logger: logging.Logger = get_logger(__name__)

_ACTIVE_STATUSES = (OrderStatus.ACTIVE, OrderStatus.REVISION)

class GetActiveOrdersByClient:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, client_id: str) -> list[Order]:
        try:
            stmt = (
                select(Order)
                .where(
                    Order.client_id == client_id,
                    Order.status.in_(_ACTIVE_STATUSES),
                )
            )
            return list(self.session.scalars(stmt).all())
        except SQLAlchemyError as exc:
            logger.error("[GetActiveOrdersByClient] DB error: %s", exc)
            raise DatabaseError(str(exc)) from exc

class GetLatestActiveOrderByClient:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, client_id: str) -> Optional[Order]:
        try:
            stmt = (
                select(Order)
                .where(
                    Order.client_id == client_id,
                    Order.status.in_(_ACTIVE_STATUSES),
                )
                .order_by(Order.updated_at.desc())
            )
            return self.session.scalar(stmt)
        except SQLAlchemyError as exc:
            logger.error("[GetLatestActiveOrderByClient] DB error: %s", exc)
            raise DatabaseError(str(exc)) from exc

class GetUpcomingDeadlines:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, client_id: str, limit: int = 3) -> list[Order]:
        try:
            stmt = (
                select(Order)
                .where(
                    Order.client_id == client_id,
                    Order.status.in_(_ACTIVE_STATUSES),
                    Order.due_date.isnot(None),
                )
                .order_by(Order.due_date.asc())
                .limit(limit)
            )
            return list(self.session.scalars(stmt).all())
        except SQLAlchemyError as exc:
            logger.error("[GetUpcomingDeadlines] DB error: %s", exc)
            raise DatabaseError(str(exc)) from exc

class GetProjectLifecycle:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, client_id: str) -> list[tuple[str, int]]:
        try:
            stmt = (
                select(Order.status, func.count(Order.id))
                .where(Order.client_id == client_id)
                .group_by(Order.status)
            )
            rows = self.session.execute(stmt).all()
            return [(status.name, count) for status, count in rows]
        except SQLAlchemyError as exc:
            logger.error("[GetProjectLifecycle] DB error: %s", exc)
            raise DatabaseError(str(exc)) from exc

class GetOrderByClient:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, order_id: str, client_id: str) -> Order:
        try:
            stmt = (
                select(Order)
                .where(
                    Order.id == order_id,
                    Order.client_id == client_id,
                )
            )
            order = self.session.scalar(stmt)
            if not order:
                raise NotFound(f"Order {order_id} not found for client {client_id}")
            return order
        except NotFound:
            raise
        except SQLAlchemyError as exc:
            logger.error("[GetOrderByClient] DB error: %s", exc)
            raise DatabaseError(str(exc)) from exc

class GetOrderForReorder:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, order_id: str, client_id: str) -> Order:
        try:
            stmt = (
                select(Order)
                .where(
                    Order.id == order_id,
                    Order.client_id == client_id,
                )
            )
            order = self.session.scalar(stmt)
            if not order:
                raise NotFound(f"Order {order_id} not found for client {client_id}")
            return order
        except NotFound:
            raise
        except SQLAlchemyError as exc:
            logger.error("[GetOrderForReorder] DB error: %s", exc)
            raise DatabaseError(str(exc)) from exc


class CreateOrderFromReorder:
    def __init__(self, session: Session) -> None:
        self.session = session

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
            self.session.add(new_order)
            self.session.flush()
            return new_order
        except SQLAlchemyError as exc:
            logger.error("[CreateOrderFromReorder] DB error: %s", exc)
            raise DatabaseError(str(exc)) from exc
