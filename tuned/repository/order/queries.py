from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy import func, select, asc, desc, or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from typing import Any, Optional, Sequence

from tuned.models import Order
from tuned.models.enums import OrderStatus
from tuned.repository.exceptions import NotFound, DatabaseError
from tuned.core.logging import get_logger
from tuned.dtos import OrderListRequestDTO, OrderListResponseDTO, OrderResponseDTO

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

def getOrderListResponse(
    session: Session, stmt: Any, req: OrderListRequestDTO
) -> OrderListResponseDTO:
    if req.service_id:
        stmt = stmt.where(Order.service_id == req.service_id)
        
    if req.q:
        search_pattern = f"%{req.q}%"
        stmt = stmt.where(
            or_(
                Order.title.ilike(search_pattern),
                Order.instructions.ilike(search_pattern),
                # Order.content.ilike(search_pattern)
            )
        )
    
    if req.academic_level_id:
        stmt = stmt.where(Order.academic_level_id == req.academic_level_id)
        
    # if req.deadline_id:
    #     stmt = stmt.where(Order.deadline_id == req.deadline_id)
    
    if req.status:
        stmt = stmt.where(Order.status == req.status)

    sort_map = {
        "due_date": Order.due_date,
        "created_at": Order.created_at,
        "title": Order.title,
    }

    sort_field = sort_map.get(req.sort or "created_at", Order.created_at)
    order_func = asc if req.order == "asc" else desc

    stmt = stmt.order_by(order_func(sort_field))

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = session.execute(count_stmt).scalar() or 0

    page = max(req.page or 1, 1)
    per_page = min(req.per_page or 10, 100)

    stmt = stmt.offset((page - 1) * per_page).limit(per_page)
    items: Sequence[Order] = session.scalars(stmt).all()

    return OrderListResponseDTO(
        orders=[OrderResponseDTO.from_model(s) for s in items],
        total=total,
        page=page,
        per_page=per_page,
        sort=req.sort,
        order=req.order,
    )

class GetClientOrders:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, client_id: str, req: OrderListRequestDTO) -> OrderListResponseDTO:
        try:
            stmt = (
                select(Order)
                .where(Order.client_id == client_id)
            )
            return getOrderListResponse(self.session, stmt, req)
        except SQLAlchemyError as exc:
            logger.error("[GetClientOrders] DB error: %s", exc)
            raise DatabaseError(str(exc)) from exc