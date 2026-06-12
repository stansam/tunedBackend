from __future__ import annotations
from dataclasses import dataclass

@dataclass
class AdminNavStatsDTO:
    active_orders_count: int      # PENDING + ACTIVE + REVISION orders
    payments_count: int            # Unpaid completed orders awaiting payment
    chat_count: int                # Unread admin comments (is_admin=False)
    testimonials_count: int        # Pending testimonials awaiting approval
