from __future__ import annotations
import logging
from typing import TYPE_CHECKING
from tuned.core.logging import get_logger
from tuned.dtos.admin import (
    AdminNavStatsDTO, AdminKPIDTO, AdminDashboardAnalyticsDTO,
    AdminDashboardTrackingDTO, AdminDashboardAlertsDTO
)

if TYPE_CHECKING:
    from tuned.repository import Repository
    from tuned.interface import Services

logger = get_logger(__name__)


class AdminAnalyticsService:
    """Service layer class for administrative analytics and navigation stats."""

    def __init__(self, repos: Repository, interfaces: Services) -> None:
        self._repos = repos
        self._repo = repos.admin_analytics
        self._interfaces = interfaces

    def get_nav_stats(self) -> AdminNavStatsDTO:
        """Return aggregated badge counts for the admin sidebar, computed via other service methods."""
        try:
            active_orders_count = self._interfaces.order.get_active_orders_count()
            payments_count = self._interfaces.order.get_unpaid_completed_orders_count()
            chat_count = self._interfaces.order.get_unread_comments_count()
            
            pending_testimonials = self._interfaces.testimonial.list_pending_testimonials()
            testimonials_count = len(pending_testimonials)

            return AdminNavStatsDTO(
                active_orders_count=active_orders_count,
                payments_count=payments_count,
                chat_count=chat_count,
                testimonials_count=testimonials_count,
            )
        except Exception as exc:
            logger.error("[AdminAnalyticsService.get_nav_stats] Error: %r", exc)
            raise

    def get_kpis(self) -> AdminKPIDTO:
        """Fetch platform KPIs for admin dashboard."""
        return self._repo.get_kpis()

    def get_analytics(self) -> AdminDashboardAnalyticsDTO:
        """Fetch analytics charts data for admin dashboard."""
        return self._repo.get_analytics()

    def get_tracking(self) -> AdminDashboardTrackingDTO:
        """Fetch deadline tracking and activity feed for admin dashboard."""
        return self._repo.get_tracking()

    def get_alerts(self) -> AdminDashboardAlertsDTO:
        """Fetch actionable alerts for admin dashboard."""
        return self._repo.get_alerts()
