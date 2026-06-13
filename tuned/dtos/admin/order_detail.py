from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from tuned.models.order import Order


@dataclass
class AdminOrderDetailResponseDTO:
    """Extends OrderDetailsResponseDTO with admin-specific fields."""
    id: str
    order_number: str
    client_id: str
    client_username: str
    status: str
    paid: bool
    escalated: bool
    extension_requested: bool
    total_price: Optional[str]
    service_id: str
    service_name: Optional[str]
    academic_level_id: str
    academic_level_name: Optional[str]
    deadline_id: str
    title: Optional[str]
    instructions: Optional[str]
    word_count: Optional[int]
    page_count: Optional[str]
    format_style: Optional[str]
    sources: Optional[int]
    line_spacing: Optional[str]
    due_date: Optional[str]
    report_type: Optional[str]
    discount_amount: Optional[str]
    created_at: str
    attachments: list  # list[OrderFileResponseDTO]

    @classmethod
    def from_model(cls, order: Order) -> AdminOrderDetailResponseDTO:
        from tuned.dtos.order import OrderFileResponseDTO
        return cls(
            id=str(order.id),
            order_number=order.order_number,
            client_id=str(order.client_id),
            client_username=order.client.username if order.client else "Unknown",
            status=order.status.value,
            paid=order.paid,
            escalated=order.escalated or False,
            extension_requested=order.extension_requested or False,
            total_price=str(order.total_price) if order.total_price else "0.0",
            service_id=str(order.service_id) if order.service_id else "",
            service_name=order.service.name if order.service else None,
            academic_level_id=str(order.academic_level_id) if order.academic_level_id else "",
            academic_level_name=order.academic_level.name if order.academic_level else None,
            deadline_id=str(order.deadline_id) if order.deadline_id else "",
            title=order.title,
            instructions=order.instructions,
            word_count=order.word_count,
            page_count=str(order.page_count) if order.page_count else "0.0",
            format_style=order.format_style.value if order.format_style else None,
            sources=order.sources,
            line_spacing=order.line_spacing.value if order.line_spacing else None,
            due_date=order.due_date.isoformat() if order.due_date else None,
            report_type=order.report_type.value if order.report_type else None,
            discount_amount=str(order.discount_amount) if order.discount_amount else "0.0",
            created_at=order.created_at.isoformat(),
            attachments=[OrderFileResponseDTO.from_model(f) for f in order.files],
        )
