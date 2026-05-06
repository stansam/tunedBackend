from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from tuned.models.order import Order

from tuned.models.enums import OrderStatus, Priority, FormatStyle, LineSpacing, ReportType

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
    def from_model(cls, order: "Order") -> "OrderProgressDTO":
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
    def from_model(cls, order: "Order") -> "UpcomingDeadlineDTO":
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


@dataclass
class CreateOrderRequestDTO:
    service_id: str
    academic_level_id: str
    deadline_id: str
    title: str
    description: str
    word_count: int
    page_count: float
    format_style: FormatStyle
    sources: int
    line_spacing: LineSpacing
    instructions: Optional[str] = None
    report_type: Optional[ReportType] = None
    discount_code: Optional[str] = None
    points_to_redeem: int = 0

    def __post_init__(self):
        if isinstance(self.format_style, str):
            self.format_style = FormatStyle(self.format_style)
        if isinstance(self.line_spacing, str):
            self.line_spacing = LineSpacing(self.line_spacing)
        if isinstance(self.report_type, str):
            self.report_type = ReportType(self.report_type)


@dataclass
class CreateOrderResponseDTO:
    order_id: str
    order_number: str
    success: bool
    message: str


@dataclass
class ValidateDiscountRequestDTO:
    code: str
    subtotal: float


@dataclass
class ValidateDiscountResponseDTO:
    valid: bool
    discount_amount: float
    description: Optional[str] = None


@dataclass
class OrderFileUploadResponseDTO:
    uploaded_count: int
    file_ids: list[str]


@dataclass
class OrderDraftCreateDTO:
    user_id: str
    service_id: Optional[str] = None
    academic_level_id: Optional[str] = None
    deadline_id: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    word_count: Optional[int] = None
    page_count: Optional[float] = None
    format_style: Optional[FormatStyle] = None
    sources: Optional[int] = None
    line_spacing: Optional[LineSpacing] = None
    report_type: Optional[ReportType] = None
    discount_code: Optional[str] = None
    points_to_redeem: int = 0

    def __post_init__(self):
        if isinstance(self.format_style, str) and self.format_style:
            self.format_style = FormatStyle(self.format_style)
        if isinstance(self.line_spacing, str) and self.line_spacing:
            self.line_spacing = LineSpacing(self.line_spacing)
        if isinstance(self.report_type, str) and self.report_type:
            self.report_type = ReportType(self.report_type)


@dataclass
class OrderDraftResponseDTO:
    id: str
    status: str
    service_id: Optional[str]
    academic_level_id: Optional[str]
    deadline_id: Optional[str]
    title: Optional[str]
    description: Optional[str]
    word_count: Optional[int]
    page_count: Optional[float]
    format_style: Optional[str]
    sources: Optional[int]
    line_spacing: Optional[str]
    report_type: Optional[str]
    discount_amount: Optional[float]

    @classmethod
    def from_model(cls, order: "Order") -> "OrderDraftResponseDTO":
        return cls(
            id=str(order.id),
            status=order.status.value,
            service_id=str(order.service_id) if order.service_id else None,
            academic_level_id=str(order.academic_level_id) if order.academic_level_id else None,
            deadline_id=str(order.deadline_id) if order.deadline_id else None,
            title=order.title,
            description=order.description,
            word_count=order.word_count,
            page_count=order.page_count,
            format_style=order.format_style.value if order.format_style else None,
            sources=order.sources,
            line_spacing=order.line_spacing.value if order.line_spacing else None,
            report_type=order.report_type.value if order.report_type else None,
            discount_amount=order.discount_amount
        )
