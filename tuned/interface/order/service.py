from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from tuned.core.logging import get_logger
from tuned.dtos.audit import ActivityLogCreateDTO
from tuned.dtos.dashboard import (
    ActionableAlertDTO,
    ActionableAlertDTO as _AlertDTO,
    ActivityFeedEntryDTO,
    ChartDataDTO,
    DashboardAlertsDTO,
    DashboardAnalyticsDTO,
    DashboardKPIDTO,
    DashboardTrackingDTO,
    NavStatsDTO,
    SpendingVelocityDTO,
)
from tuned.dtos.order import (
    OrderProgressDTO,
    ReorderResponseDTO,
    UpcomingDeadlineDTO,
)
from tuned.interface.audit import audit_service
from tuned.repository import repositories
from tuned.repository.exceptions import DatabaseError, NotFound

logger: logging.Logger = get_logger(__name__)


class OrderService:
    def __init__(self) -> None:
        self._repo  = repositories.order
        self._audit = audit_service.activity_log

    def get_nav_stats(self, user_id: str) -> NavStatsDTO:
        """
        # TODO: implement wallet balance calculation once wallet model exists
        """
        try:
            active_orders = self._repo.get_active_orders(user_id)
            return NavStatsDTO(
                active_orders=len(active_orders),
                balance=0.0,  # TODO: implement wallet balance calculation
            )
        except DatabaseError:
            logger.error("[OrderService.get_nav_stats] DB error for user %s", user_id)
            raise

    def get_kpis(self, user_id: str) -> DashboardKPIDTO:
        try:
            from tuned.repository.user.get import GetUserByID
            from tuned.extensions import db as _db

            active_orders = self._repo.get_active_orders(user_id)

            portfolio_value = sum(o.total_price for o in active_orders)

            due_dates = [o.due_date for o in active_orders if o.due_date]
            next_deadline: Optional[str] = (
                min(due_dates).isoformat() if due_dates else None
            )

            user = GetUserByID(_db.session).execute(user_id)
            reward_points: int = user.reward_points or 0

            return DashboardKPIDTO(
                active_projects=len(active_orders),
                portfolio_value=round(portfolio_value, 2),
                reward_points=reward_points,
                next_deadline=next_deadline,
            )
        except DatabaseError:
            logger.error("[OrderService.get_kpis] DB error for user %s", user_id)
            raise

    def get_analytics(self, user_id: str) -> DashboardAnalyticsDTO:
        try:
            spending_raw   = self._repo.get_spending_velocity(user_id)
            lifecycle_raw  = self._repo.get_project_lifecycle(user_id)
            service_mix_raw = self._repo.get_service_mix(user_id)
            referral_raw   = self._repo.get_referral_growth(user_id)

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
            logger.error("[OrderService.get_analytics] DB error for user %s", user_id)
            raise

    def get_tracking(self, user_id: str) -> DashboardTrackingDTO:
        try:
            latest      = self._repo.get_latest_active_order(user_id)
            deadlines   = self._repo.get_upcoming_deadlines(user_id, limit=3)
            log_entries = self._repo.get_activity_feed(user_id, limit=10)

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
            logger.error("[OrderService.get_tracking] DB error for user %s", user_id)
            raise

    def get_alerts(self, user_id: str) -> DashboardAlertsDTO:
        try:
            alerts = self._repo.get_actionable_alerts(user_id)
            return DashboardAlertsDTO(alerts=alerts)
        except DatabaseError:
            logger.error("[OrderService.get_alerts] DB error for user %s", user_id)
            raise

    def reorder(self, order_id: str, user_id: str) -> ReorderResponseDTO:
        try:
            source    = self._repo.get_order_for_reorder(order_id, user_id)
            new_order = self._repo.create_reorder(source, user_id)

            # Audit
            try:
                self._audit.log(ActivityLogCreateDTO(
                    action="order_reordered",
                    user_id=user_id,
                    entity_type="Order",
                    entity_id=str(new_order.id),
                    after={"source_order_id": order_id},
                    created_by=user_id,
                ))
            except Exception as audit_exc:
                logger.error(
                    "[OrderService.reorder] Audit failed for new order %s: %r",
                    new_order.id, audit_exc,
                )

            try:
                from tuned.core.events import get_event_bus
                get_event_bus().emit("order.created", {
                    "order_id":     str(new_order.id),
                    "client_id":    user_id,
                    "order_number": new_order.order_number,
                })
            except Exception as event_exc:
                logger.error(
                    "[OrderService.reorder] Event emit failed for %s: %r",
                    new_order.id, event_exc,
                )

            logger.info(
                "[OrderService.reorder] User %s reordered %s → new order %s",
                user_id, order_id, new_order.order_number,
            )
            return ReorderResponseDTO(
                order_id=str(new_order.id),
                order_number=new_order.order_number,
                redirect_url=f"/client/orders/{new_order.id}",
            )

        except NotFound:
            logger.warning(
                "[OrderService.reorder] Order %s not found for user %s",
                order_id, user_id,
            )
            raise
        except DatabaseError:
            logger.error(
                "[OrderService.reorder] DB error for order %s user %s",
                order_id, user_id,
            )
            raise
