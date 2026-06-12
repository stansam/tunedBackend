from __future__ import annotations
import logging
from typing import TYPE_CHECKING
from tuned.core.logging import get_logger
from tuned.dtos.admin.nav import AdminNavStatsDTO

if TYPE_CHECKING:
    from tuned.interface import Services

logger = get_logger(__name__)


class AdminAnalyticsService:
    """Service layer class for administrative analytics and navigation stats."""

    def __init__(self, interfaces: Services) -> None:
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
