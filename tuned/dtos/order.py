from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Optional

from tuned.models.enums import OrderStatus, Priority

_STATUS_PROGRESS: dict[OrderStatus, int] = {
    OrderStatus.PENDING:                   0,
    OrderStatus.ACTIVE:                   40,
    OrderStatus.REVISION:                 60,
    OrderStatus.COMPLETED_PENDING_REVIEW: 80,
    OrderStatus.COMPLETED:               100,
    OrderStatus.OVERDUE:                  30,
    OrderStatus.CANCELED:                  0,
}


def derive_progress(status: OrderStatus) -> int:
    return _STATUS_PROGRESS.get(status, 0)


def derive_priority(due_date: Optional[datetime]) -> Priority:
    if due_date is None:
        return Priority.LOW

    now = datetime.now(timezone.utc)
    if due_date.tzinfo is None:
        due_date = due_date.replace(tzinfo=timezone.utc)

    delta = due_date - now
    if delta <= timedelta(hours=24):
        return Priority.URGENT
    if delta <= timedelta(hours=72):
        return Priority.HIGH
    if delta <= timedelta(days=7):
        return Priority.NORMAL
    return Priority.LOW


def _status_to_string(status: OrderStatus) -> str:
    return status.name

@dataclass
class OrderProgressDTO:
    id:           str
    order_number: str
    status:       str
    progress:     int
    delivered_at: Optional[str]

    @classmethod
    def from_model(cls, order: object) -> "OrderProgressDTO":
        return cls(
            id=str(order.id),
            order_number=order.order_number,
            status=_status_to_string(order.status),
            progress=derive_progress(order.status),
            delivered_at=(
                order.delivered_at.isoformat()
                if order.delivered_at else None
            ),
        )


@dataclass
class UpcomingDeadlineDTO:
    id:           str
    order_number: str
    title:        str
    due_date:     str
    priority:     str

    @classmethod
    def from_model(cls, order: object) -> "UpcomingDeadlineDTO":
        due_date_dt: Optional[datetime] = order.due_date
        return cls(
            id=str(order.id),
            order_number=order.order_number,
            title=order.title,
            due_date=due_date_dt.isoformat() if due_date_dt else "",
            priority=derive_priority(due_date_dt).name,
        )


@dataclass
class ReorderResponseDTO:
    order_id:     str
    order_number: str
    redirect_url: str
