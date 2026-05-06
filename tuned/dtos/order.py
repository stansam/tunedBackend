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

class OrderResponseDTO:
    id: str
    order_number: str
    client_id: str
    status: OrderStatus
    paid: bool
    total_price: float
    service_id: str
    academic_level_id: str
    deadline_id: str
    title: str
    instructions: str
    word_count: int
    page_count: float
    format_style: FormatStyle
    sources: int
    line_spacing: LineSpacing
    due_date: datetime
    report_type: Optional[ReportType]
    discount_amount: Optional[float]

    @classmethod
    def from_model(cls, order: "Order") -> "OrderResponseDTO":
        return cls(
            id=str(order.id),
            order_number=order.order_number,
            client_id=str(order.client_id),
            status=order.status.value,
            paid=order.paid,
            total_price=order.total_price,
            service_id=str(order.service_id),
            academic_level_id=str(order.academic_level_id),
            deadline_id=str(order.deadline_id),
            title=order.title,
            instructions=order.instructions,
            word_count=order.word_count,
            page_count=order.page_count,
            format_style=order.format_style.value,
            sources=order.sources,
            line_spacing=order.line_spacing.value,
            due_date=order.due_date.isoformat() if order.due_date else None,
            report_type=order.report_type.value if order.report_type else None,
            discount_amount=order.discount_amount
        )

class OrderListRequestDTO:
    # user_id: str
    status: Optional[str] = None
    q: Optional[str] = None
    sort: Optional[str] = "created_at"
    order: Optional[str] = "desc"
    page: Optional[int] = 1
    per_page: Optional[int] = 10
    service_id: Optional[str] = None
    academic_level_id: Optional[str] = None
    # deadline_id: Optional[str] = None

    def __post_init__(self):
        if isinstance(self.status, str):
            self.status = OrderStatus(self.status)
        if isinstance(self.sort, str):
            self.sort = self.sort.strip()
        if isinstance(self.order, str):
            self.order = self.order.strip().lower()
        if isinstance(self.page, str):
            self.page = int(self.page)
        if isinstance(self.per_page, str):
            self.per_page = int(self.per_page)
        if isinstance(self.service_id, str):
            self.service_id = self.service_id.strip()
        if isinstance(self.academic_level_id, str):
            self.academic_level_id = self.academic_level_id.strip()
        # if isinstance(self.deadline_id, str):
        #     self.deadline_id = self.deadline_id.strip()

    # def to_dict(self) -> dict[str, Any]:
    #     return {
    #         "user_id": self.user_id,
    #         "status": self.status,
    #         "q": self.q,
    #         "sort": self.sort,
    #         "order": self.order,
    #         "page": self.page,
    #         "per_page": self.per_page,
    #         "service_id": self.service_id,
    #         "academic_level_id": self.academic_level_id,
    #         "deadline_id": self.deadline_id,
    #     }

class OrderListResponseDTO:
    orders: list[OrderResponseDTO]
    total: int
    page: int
    per_page: int
    sort: str
    order: str

    def __init__(
        self,
        orders: list[OrderResponseDTO],
        total: int,
        page: int,
        per_page: int,
        sort: str,
        order: str,
    ) -> None:
        self.orders = orders
        self.total = total
        self.page = page
        self.per_page = per_page
        self.sort = sort
        self.order = order

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
    level_id: str
    title: str
    # description: str
    word_count: int
    page_count: float
    format_style: FormatStyle
    sources: int
    line_spacing: LineSpacing
    due_date: datetime
    deadline_id: Optional[str] = ""
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
    # success: bool
    # message: str

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
    instructions: Optional[str] = None
    word_count: Optional[int] = None
    page_count: Optional[float] = None
    format_style: Optional[FormatStyle] = None
    sources: Optional[int] = None
    line_spacing: Optional[LineSpacing] = None
    due_date: Optional[datetime] = None
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
    instructions: Optional[str]
    word_count: Optional[int]
    page_count: Optional[float]
    format_style: Optional[str]
    sources: Optional[int]
    line_spacing: Optional[str]
    due_date: Optional[datetime]
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
            instructions=order.instructions,
            word_count=order.word_count,
            page_count=order.page_count,
            format_style=order.format_style.value if order.format_style else None,
            sources=order.sources,
            line_spacing=order.line_spacing.value if order.line_spacing else None,
            due_date=order.due_date.isoformat() if order.due_date else None,
            report_type=order.report_type.value if order.report_type else None,
            discount_amount=order.discount_amount
        )