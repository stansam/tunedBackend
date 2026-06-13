from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from tuned.models.deadline_extension import OrderDeadlineExtensionRequest


@dataclass
class AdminDeadlineExtensionResponseDTO:
    id: str
    order_id: str
    requested_hours: int
    reason: str
    client_notes: Optional[str]
    status: str
    status_color: str
    priority: str
    original_due_date: str
    new_due_date: Optional[str]
    hours_granted: Optional[int]
    is_pending: bool
    rejection_reason: Optional[str]
    requested_at: str
    reviewed_at: Optional[str]
    requester_name: str
    reviewer_name: Optional[str]

    @classmethod
    def from_model(cls, r: OrderDeadlineExtensionRequest) -> AdminDeadlineExtensionResponseDTO:
        return cls(
            id=str(r.id),
            order_id=str(r.order_id),
            requested_hours=r.requested_hours,
            reason=r.reason,
            client_notes=r.client_notes,
            status=r.status.value,
            status_color=r.status_color,
            priority=r.priority.value,
            original_due_date=r.original_due_date.isoformat() if r.original_due_date else "",
            new_due_date=r.new_due_date.isoformat() if r.new_due_date else None,
            hours_granted=r.hours_difference,
            is_pending=r.is_pending,
            rejection_reason=r.rejection_reason if r.status.value == "rejected" else None,
            requested_at=r.requested_at.isoformat() if r.requested_at else "",
            reviewed_at=r.reviewed_at.isoformat() if r.reviewed_at else None,
            requester_name=r.requester.get_name() if r.requester else "Unknown",
            reviewer_name=r.reviewer.get_name() if r.reviewer else None,
        )
