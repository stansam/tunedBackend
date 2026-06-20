from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from tuned.models.order import Order


@dataclass
class AdminOrderResponseDTO:
    """Admin-specific order representation with client and service data."""
    id: str
    order_number: str
    client_id: str
    client_name: str          # client username
    status: str               # lowercase status string
    paid: bool
    total_price: str          # Decimal as string
    service_id: str
    service_name: str         # service name
    due_date: Optional[str]   # ISO 8601 or None
    escalated: bool

    @classmethod
    def from_model(cls, order: "Order") -> "AdminOrderResponseDTO":
        return cls(
            id=str(order.id),
            order_number=order.order_number,
            client_id=str(order.client_id),
            client_name=order.client.username if order.client else "Unknown",
            status=order.status.value if order.status else "draft",
            paid=order.paid,
            total_price=str(order.total_price) if order.total_price else "0.00",
            service_id=str(order.service_id) if order.service_id else "",
            service_name=order.service.name if order.service else "Unknown",
            due_date=order.due_date.isoformat() if order.due_date else None,
            escalated=order.escalated or False,
        )


@dataclass
class AdminOrderListResponseDTO:
    orders: list[AdminOrderResponseDTO]
    total: int
    page: int
    per_page: int
    sort: str
    order: str


@dataclass
class AdminOrdersStatsDTO:
    """Count-by-status stats."""
    all: int
    pending: int
    in_progress: int         # ACTIVE + REVISION
    revision: int
    completed: int
    overdue: int


@dataclass
class AdminBottleneckStatsDTO:
    """Bottleneck counts where orders are delayed or stuck."""
    pending_activation: int   # PENDING status orders
    under_review: int          # COMPLETED_PENDING_REVIEW status orders
    awaiting_payment: int      # unpaid non-draft orders


@dataclass
class AdminServiceLoadDTO:
    """Active orders count per service."""
    id: str
    name: str
    orders_count: int
    status: str              # "Busy" | "OK" | "Free"


@dataclass
class AdminOrdersStatsResponseDTO:
    stats: AdminOrdersStatsDTO
    bottlenecks: AdminBottleneckStatsDTO
    service_load: list[AdminServiceLoadDTO]
