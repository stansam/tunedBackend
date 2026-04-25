from __future__ import annotations

from typing import Optional

from tuned.extensions import db
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
    def __init__(self) -> None:
        self.db = db

    def get_active_orders(self, client_id: str) -> list[Order]:
        return GetActiveOrdersByClient(self.db.session).execute(client_id)
    def get_latest_active_order(self, client_id: str) -> Optional[Order]:
        return GetLatestActiveOrderByClient(self.db.session).execute(client_id)
    def get_upcoming_deadlines(self, client_id: str, limit: int = 3) -> list[Order]:
        return GetUpcomingDeadlines(self.db.session).execute(client_id, limit)

    def get_project_lifecycle(self, client_id: str) -> list[tuple[str, int]]:
        return GetProjectLifecycle(self.db.session).execute(client_id)

    def get_order_for_reorder(self, order_id: str, client_id: str) -> Order:
        return GetOrderForReorder(self.db.session).execute(order_id, client_id)
    def create_reorder(self, source: Order, client_id: str) -> Order:
        return CreateOrderFromReorder(self.db.session).execute(source, client_id)
