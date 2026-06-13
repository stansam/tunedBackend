from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from tuned.models.user import User


def derive_clv_status(total_spent: float) -> str:
    """Customer Lifetime Value status derived from total spending."""
    if total_spent >= 500:
        return "high"
    if total_spent >= 100:
        return "medium"
    if total_spent > 0:
        return "low"
    return "normal"


def derive_user_status(last_order_at: Optional[str]) -> str:
    """Active if ordered in last 30 days, dormant otherwise."""
    if not last_order_at:
        return "dormant"
    from datetime import datetime, timezone, timedelta
    try:
        last = datetime.fromisoformat(last_order_at.replace("Z", "+00:00"))
        if datetime.now(timezone.utc) - last <= timedelta(days=30):
            return "active"
    except ValueError:
        pass
    return "dormant"


@dataclass
class AdminUserInsightDTO:
    id: str
    name: str                    # username
    email: str
    avatar_url: Optional[str]
    orders_count: int
    total_spent: str             # Decimal as string
    clv_status: str              # "high" | "medium" | "low" | "normal"
    last_order_at: Optional[str] # ISO 8601 or None
    status: str                  # "active" | "dormant"


@dataclass
class AdminUserListResponseDTO:
    users: list[AdminUserInsightDTO]
    total: int
    page: int
    per_page: int


@dataclass
class AdminUserStatsDTO:
    total_clients: int
    total_clients_growth_this_month: int
    returning_clients_percentage: float
    returning_clients_growth_vs_last_month: float
    dormant_clients_count: int
    high_value_clients_count: int
    client_retention_rate: float


@dataclass
class GeographicDistributionDTO:
    country_code: str       # 2–3 char ISO or "OT" for other
    country_name: str
    percentage: float


@dataclass
class AdminUserListRequestDTO:
    status: Optional[str] = None      # "active" | "dormant" | None (all)
    clv_status: Optional[str] = None  # "high" | "medium" | "low" | "normal" | None
    q: Optional[str] = None
    sort: Optional[str] = "created_at"
    order: Optional[str] = "desc"
    page: int = 1
    per_page: int = 5
