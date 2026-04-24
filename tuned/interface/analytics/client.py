from __future__ import annotations

import logging
from typing import Optional

from tuned.core.logging import get_logger
from tuned.dtos import (
    ActivityFeedEntryDTO,
    ChartDataDTO,
    DashboardAlertsDTO,
    DashboardAnalyticsDTO,
    DashboardKPIDTO,
    DashboardTrackingDTO,
    NavStatsDTO,
    SpendingVelocityDTO,
    ActivityLogFilterDTO
)
from tuned.dtos.order import (
    OrderProgressDTO,
    UpcomingDeadlineDTO,
)
# from tuned.interface.audit import audit_service
from tuned.utils.variables import Variables
from tuned.repository import repositories
from tuned.repository.exceptions import DatabaseError

logger: logging.Logger = get_logger(__name__)


class AnalyticsService:
    def __init__(self) -> None:
        self._order_repo  = repositories.order
        self._user_repo = repositories.user
        self._payment_repo = repositories.payment.payment
        self._service_repo = repositories.service
        self._audit_repo = repositories.audit.activity_log

    def get_nav_stats(self, user_id: str) -> NavStatsDTO:
        """
        # TODO: implement wallet balance calculation once wallet model exists
        """
        try:
            active_orders = self._order_repo.get_active_orders(user_id)
            return NavStatsDTO(
                active_orders=len(active_orders),
                balance=0.0,  # TODO: implement wallet balance calculation
            )
        except DatabaseError:
            logger.error("[AnalyticsService.get_nav_stats] DB error for user %s", user_id)
            raise

    def get_kpis(self, user_id: str) -> DashboardKPIDTO:
        try:

            active_orders = self._order_repo.get_active_orders(user_id)

            portfolio_value = sum(o.total_price for o in active_orders)

            due_dates = [o.due_date for o in active_orders if o.due_date]
            next_deadline: Optional[str] = (
                min(due_dates).isoformat() if due_dates else None
            )

            user = self._user_repo.get_user_by_id(user_id)
            reward_points: int = user.reward_points or 0

            return DashboardKPIDTO(
                active_projects=len(active_orders),
                portfolio_value=round(portfolio_value, 2),
                reward_points=reward_points,
                next_deadline=next_deadline,
            )
        except DatabaseError:
            logger.error("[AnalyticsService.get_kpis] DB error for user %s", user_id)
            raise

    def get_analytics(self, user_id: str) -> DashboardAnalyticsDTO:
        try:
            spending_raw   = self._payment_repo.get_spending_velocity(user_id)
            lifecycle_raw  = self._order_repo.get_project_lifecycle(user_id)
            service_mix_raw = self._service_repo.get_service_mix(user_id)
            referral_raw   = self._user_repo.get_referral_growth(user_id)

            return DashboardAnalyticsDTO(
                spending_velocity=[
                    SpendingVelocityDTO(month=m, amount=amt)
                    for m, amt in spending_raw
                ],
                project_lifecycle=[
                    ChartDataDTO(name=status, value=float(count))
                    for status, count in lifecycle_raw
                ],
                service_mix=[
                    ChartDataDTO(name=cat, value=float(count))
                    for cat, count in service_mix_raw
                ],
                referral_growth=[
                    ChartDataDTO(name=m, value=amt)
                    for m, amt in referral_raw
                ],
            )
        except DatabaseError:
            logger.error("[AnalyticsService.get_analytics] DB error for user %s", user_id)
            raise

    def get_tracking(self, user_id: str) -> DashboardTrackingDTO:
        try:
            latest      = self._order_repo.get_latest_active_order(user_id)
            deadlines   = self._order_repo.get_upcoming_deadlines(user_id, limit=3)
            log_filter = ActivityLogFilterDTO(
                user_id=user_id,
                action=Variables.USER_LOGIN_ACTION,
                per_page=10,
                page=1,
            )
            log_entries, _ = self._audit_repo.get_filtered(log_filter)

            return DashboardTrackingDTO(
                latest_order=(
                    OrderProgressDTO.from_model(latest) if latest else None
                ),
                upcoming_deadlines=[
                    UpcomingDeadlineDTO.from_model(o) for o in deadlines
                ],
                activity_feed=[
                    ActivityFeedEntryDTO.from_model(e) for e in log_entries
                ],
            )
        except DatabaseError:
            logger.error("[AnalyticsService.get_tracking] DB error for user %s", user_id)
            raise

    def get_alerts(self, user_id: str) -> DashboardAlertsDTO:
        try:
            alerts = self._user_repo.get_actionable_alerts(user_id)
            return DashboardAlertsDTO(alerts=alerts)
        except DatabaseError:
            logger.error("[AnalyticsService.get_alerts] DB error for user %s", user_id)
            raise