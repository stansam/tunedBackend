import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, TypeVar, Generic, TYPE_CHECKING, Any
from tuned.models.enums import EmailStatus
if TYPE_CHECKING:
    from tuned.models.audit import PriceHistory, OrderStatusHistory, ActivityLog, EmailLog


T = TypeVar("T")

@dataclass
class AuditListResponseDTO(Generic[T]):
    items: List[T]
    total: int
    page: int
    per_page: int

@dataclass
class PriceHistoryCreateDTO:
    price_rate_id: str
    old_price: float
    new_price: float
    reason: Optional[str] = None
    created_by: Optional[str] = None

@dataclass
class PriceHistoryResponseDTO:
    id: str
    price_rate_id: str
    old_price: float
    new_price: float
    reason: Optional[str]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, obj: "PriceHistory") -> "PriceHistoryResponseDTO":
        return cls(
            id=str(obj.id),
            price_rate_id=str(obj.price_rate_id),
            old_price=obj.old_price,
            new_price=obj.new_price,
            reason=obj.reason,
            created_at=obj.created_at,
            updated_at=obj.updated_at
        )

@dataclass
class OrderStatusHistoryCreateDTO:
    order_id: str
    user_id: str
    new_status: str
    old_status: Optional[str] = None
    notes: Optional[str] = None
    ip_address: Optional[str] = None
    created_by: Optional[str] = None

@dataclass
class OrderStatusHistoryResponseDTO:
    id: str
    order_id: str
    user_id: str
    old_status: Optional[str]
    new_status: str
    notes: Optional[str]
    ip_address: Optional[str]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, obj: "OrderStatusHistory") -> "OrderStatusHistoryResponseDTO":
        return cls(
            id=str(obj.id),
            order_id=str(obj.order_id),
            user_id=str(obj.user_id),
            old_status=obj.old_status,
            new_status=obj.new_status,
            notes=obj.notes,
            ip_address=obj.ip_address,
            created_at=obj.created_at,
            updated_at=obj.updated_at
        )

@dataclass
class ActivityLogCreateDTO:
    action: str
    user_id: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    before: Any = None
    after: Any = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_by: Optional[str] = None

@dataclass
class ActivityLogResponseDTO:
    id: str
    user_id: Optional[str]
    action: str
    entity_type: Optional[str]
    entity_id: Optional[str]
    before: Any
    after: Any
    ip_address: Optional[str]
    user_agent: Optional[str]
    created_at: datetime

    @classmethod
    def from_model(cls, obj: "ActivityLog") -> "ActivityLogResponseDTO":
        return cls(
            id=str(obj.id),
            user_id=str(obj.user_id) if obj.user_id else None,
            action=obj.action,
            entity_type=obj.entity_type,
            entity_id=str(obj.entity_id) if obj.entity_id else None,
            before=obj.before,
            after=obj.after,
            ip_address=obj.ip_address,
            user_agent=obj.user_agent,
            created_at=obj.created_at
        )

@dataclass
class ActivityLogFilterDTO:
    user_id: Optional[str] = None
    action: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    page: int = 1
    per_page: int = 20
    sort: str = "created_at"
    order: str = "desc"

@dataclass
class EmailLogCreateDTO:
    recipient: str
    subject: str
    template: Optional[str] = None
    user_id: Optional[uuid.UUID] = None
    order_id: Optional[uuid.UUID] = None
    created_by: Optional[uuid.UUID] = None

@dataclass
class EmailLogResponseDTO:
    id: str
    recipient: str
    subject: str
    template: Optional[str]
    status: str
    error_message: Optional[str]
    sent_at: Optional[datetime]
    user_id: Optional[str]
    order_id: Optional[str]
    created_at: datetime

    @classmethod
    def from_model(cls, obj: "EmailLog") -> "EmailLogResponseDTO":
        return cls(
            id=str(obj.id),
            recipient=obj.recipient,
            subject=obj.subject,
            template=obj.template,
            status=obj.status,
            error_message=obj.error_message,
            sent_at=obj.sent_at,
            user_id=str(obj.user_id) if obj.user_id else None,
            order_id=str(obj.order_id) if obj.order_id else None,
            created_at=obj.created_at
        )

@dataclass
class EmailLogUpdateDTO:
    status: EmailStatus
    error_message: Optional[str] = None
    sent_at: Optional[datetime] = None

@dataclass
class EmailLogFilterDTO:
    recipient: Optional[str] = None
    status: Optional[str] = None
    user_id: Optional[str] = None
    order_id: Optional[str] = None
    page: int = 1
    per_page: int = 20
