from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import select, func
from sqlalchemy.exc import SQLAlchemyError
from tuned.models import Order
from tuned.repository.order.queries import (
    GetActiveOrdersByClient,
    GetLatestActiveOrderByClient,
    GetUpcomingDeadlines,
    GetProjectLifecycle,
    GetOrderByClient,
    GetOrderForReorder,
    CreateOrderFromReorder,
)
from tuned.repository.exceptions import DatabaseError
from tuned.repository.protocols import OrderRepositoryProtocol


class OrderRepository(OrderRepositoryProtocol):
    def __init__(self, session: Session) -> None:
        self.session = session

    def _get_order_by_id_for_client(self, order_id: str, client_id: str) -> Order:
        return GetOrderByClient(self.session).execute(order_id, client_id)

    def get_active_orders(self, client_id: str) -> list[Order]:
        return GetActiveOrdersByClient(self.session).execute(client_id)

    def get_paid_order_count(self, client_id: str) -> int:
        stmt = (
            select(func.count(Order.id))
            .where(Order.client_id == client_id, Order.paid == True)
        )
        return self.session.scalar(stmt) or 0

    def get_latest_active_order(self, client_id: str) -> Optional[Order]:
        return GetLatestActiveOrderByClient(self.session).execute(client_id)

    def get_upcoming_deadlines(self, client_id: str, limit: int = 3) -> list[Order]:
        return GetUpcomingDeadlines(self.session).execute(client_id, limit)

    def get_project_lifecycle(self, client_id: str) -> list[tuple[str, int]]:
        return GetProjectLifecycle(self.session).execute(client_id)

    def get_order_by_id_for_client(self, order_id: str, client_id: str) -> Order:
        return self._get_order_by_id_for_client(order_id, client_id)

    def get_order_for_reorder(self, order_id: str, client_id: str) -> Order:
        return GetOrderForReorder(self.session).execute(order_id, client_id)

    def apply_discount(self, order_id: str, client_id: str, discount_amount: float) -> Order:
        order = self._get_order_by_id_for_client(order_id, client_id)
        order.discount_amount = (order.discount_amount or 0.0) + discount_amount
        order.total_price = max(order.subtotal - order.discount_amount, 0.0)
        self.session.flush()
        return order

    def create_reorder(self, source: Order, client_id: str) -> Order:
        return CreateOrderFromReorder(self.session).execute(source, client_id)

    def save(self) -> None:
        try:
            self.session.commit()
        except SQLAlchemyError as exc:
            self.session.rollback()
            raise DatabaseError(f"Database error while saving order changes: {exc}") from exc

    def rollback(self) -> None:
        self.session.rollback()
