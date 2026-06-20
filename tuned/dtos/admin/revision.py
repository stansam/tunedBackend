from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from tuned.models.revision_request import OrderRevisionRequest


@dataclass
class AdminRevisionRequestResponseDTO:
    id: str
    order_id: str
    delivery_id: str
    revision_notes: str
    internal_notes: Optional[str]
    status: str
    status_color: str
    priority: str
    revision_count: int
    is_active: bool
    requested_at: str
    reviewed_at: Optional[str]
    resolved_at: Optional[str]
    estimated_completion: Optional[str]
    requester_name: str
    reviewer_name: Optional[str]

    @classmethod
    def from_model(cls, r: OrderRevisionRequest) -> AdminRevisionRequestResponseDTO:
        return cls(
            id=str(r.id),
            order_id=str(r.order_id),
            delivery_id=str(r.delivery_id),
            revision_notes=r.revision_notes,
            internal_notes=r.internal_notes,
            status=r.status.value,
            status_color=r.status_color,
            priority=r.priority.value,
            revision_count=r.revision_count,
            is_active=r.is_active,
            requested_at=r.requested_at.isoformat() if r.requested_at else "",
            reviewed_at=r.reviewed_at.isoformat() if r.reviewed_at else None,
            resolved_at=r.resolved_at.isoformat() if r.resolved_at else None,
            estimated_completion=r.estimated_completion.isoformat() if r.estimated_completion else None,
            requester_name=r.requester.get_name() if r.requester else "Unknown",
            reviewer_name=r.reviewer.get_name() if r.reviewer else None,
        )
