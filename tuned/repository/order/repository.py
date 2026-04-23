from __future__ import annotations

from typing import Optional

from tuned.extensions import db
from tuned.models import Order, ActivityLog
from tuned.dtos.dashboard import ActionableAlertDTO
from tuned.repository.order.queries import (
    GetActiveOrdersByClient,
    GetLatestActiveOrderByClient,
    GetUpcomingDeadlines,
    GetSpendingVelocity,
    GetProjectLifecycle,
    GetServiceMix,
    GetReferralGrowth,
    GetActivityFeed,
    GetActionableAlerts,
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

    def get_spending_velocity(
        self, client_id: str, months: int = 6
    ) -> list[tuple[str, float]]:
        return GetSpendingVelocity(self.db.session).execute(client_id, months)
    def get_project_lifecycle(self, client_id: str) -> list[tuple[str, int]]:
        return GetProjectLifecycle(self.db.session).execute(client_id)
    def get_service_mix(self, client_id: str) -> list[tuple[str, int]]:
        return GetServiceMix(self.db.session).execute(client_id)
    def get_referral_growth(
        self, referrer_id: str, months: int = 6
    ) -> list[tuple[str, float]]:
        return GetReferralGrowth(self.db.session).execute(referrer_id, months)

    def get_activity_feed(self, user_id: str, limit: int = 10) -> list[ActivityLog]:
        return GetActivityFeed(self.db.session).execute(user_id, limit)

    def get_actionable_alerts(self, client_id: str) -> list[ActionableAlertDTO]:
        return GetActionableAlerts(self.db.session).execute(client_id)

    def get_order_for_reorder(self, order_id: str, client_id: str) -> Order:
        return GetOrderForReorder(self.db.session).execute(order_id, client_id)
    def create_reorder(self, source: Order, client_id: str) -> Order:
        return CreateOrderFromReorder(self.db.session).execute(source, client_id)
