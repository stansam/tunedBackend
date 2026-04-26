from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session
from tuned.models import Order
from tuned.repository.order.queries import (
    GetActiveOrdersByClient,
    GetLatestActiveOrderByClient,
    GetUpcomingDeadlines,
    GetProjectLifecycle,
    GetOrderForReorder,
    CreateOrderFromReorder,
)

class OrderRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_active_orders(self, client_id: str) -> list[Order]:
        return GetActiveOrdersByClient(self.session).execute(client_id)
    def get_paid_order_count(self, client_id: str) -> int:
        return self.session.query(Order).filter(Order.client_id == client_id, Order.paid == True).count()
    def get_latest_active_order(self, client_id: str) -> Optional[Order]:
        return GetLatestActiveOrderByClient(self.session).execute(client_id)
    def get_upcoming_deadlines(self, client_id: str, limit: int = 3) -> list[Order]:
        return GetUpcomingDeadlines(self.session).execute(client_id, limit)

    def get_project_lifecycle(self, client_id: str) -> list[tuple[str, int]]:
        return GetProjectLifecycle(self.session).execute(client_id)

    def get_order_for_reorder(self, order_id: str, client_id: str) -> Order:
        return GetOrderForReorder(self.session).execute(order_id, client_id)
    def create_reorder(self, source: Order, client_id: str) -> Order:
        return CreateOrderFromReorder(self.session).execute(source, client_id)
