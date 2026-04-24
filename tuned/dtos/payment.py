from tuned.models import RefundStatus
from dataclasses import dataclass
from typing import Optional
from datetime import datetime
from tuned.dtos.base import BaseDTO

@dataclass(kw_only=True)
class PaymentCreateDTO:
    order_id: str
    user_id: str
    amount: float
    method: str
    status: Optional[str] = "pending"
    processor_id: Optional[str] = None
    processor_response: Optional[str] = None
    payer_id: Optional[str] = None

@dataclass(kw_only=True)
class PaymentUpdateDTO:
    status: Optional[str] = None
    processor_response: Optional[str] = None

@dataclass(kw_only=True)
class PaymentResponseDTO(BaseDTO):
    id: str
    payment_id: str
    order_id: str
    user_id: str
    amount: float
    status: str
    method: str
    currency: str
    
    @classmethod
    def from_model(cls, model: object) -> 'PaymentResponseDTO':
        return cls(
            id=str(model.id),
            payment_id=model.payment_id,
            order_id=model.order_id,
            user_id=model.user_id,
            amount=model.amount,
            status=model.status.value if hasattr(model.status, 'value') else model.status,
            method=model.method.value if hasattr(model.method, 'value') else model.method,
            currency=model.currency.value if hasattr(model.currency, 'value') else model.currency,
            created_at=model.created_at,
            updated_at=model.updated_at,
            is_deleted=getattr(model, 'is_deleted', False)
        )

@dataclass(kw_only=True)
class InvoiceCreateDTO:
    order_id: str
    user_id: str
    subtotal: float
    total: float
    due_date: datetime
    payment_id: Optional[str] = None
    discount: Optional[float] = 0.0
    tax: Optional[float] = 0.0
    paid: Optional[bool] = False

@dataclass(kw_only=True)
class InvoiceUpdateDTO:
    paid: Optional[bool] = None
    payment_id: Optional[str] = None

@dataclass(kw_only=True)
class InvoiceResponseDTO(BaseDTO):
    id: str
    invoice_number: str
    order_id: str
    user_id: str
    payment_id: Optional[str]
    subtotal: float
    discount: float
    tax: float
    total: float
    due_date: datetime
    paid: bool
    
    @classmethod
    def from_model(cls, model: object) -> 'InvoiceResponseDTO':
        return cls(
            id=str(model.id),
            invoice_number=model.invoice_number,
            order_id=model.order_id,
            user_id=model.user_id,
            payment_id=model.payment_id,
            subtotal=model.subtotal,
            discount=model.discount,
            tax=model.tax,
            total=model.total,
            due_date=model.due_date,
            paid=model.paid,
            created_at=model.created_at,
            updated_at=model.updated_at,
            is_deleted=getattr(model, 'is_deleted', False)
        )

@dataclass(kw_only=True)
class TransactionCreateDTO:
    payment_id: str
    transaction_id: str
    type: str
    amount: float
    status: str
    processor_id: Optional[str] = None
    processor_response: Optional[str] = None

@dataclass(kw_only=True)
class TransactionResponseDTO(BaseDTO):
    id: str
    payment_id: str
    transaction_id: str
    type: str
    amount: float
    status: str
    
    @classmethod
    def from_model(cls, model: object) -> 'TransactionResponseDTO':
        return cls(
            id=str(model.id),
            payment_id=model.payment_id,
            transaction_id=model.transaction_id,
            type=model.type.value if hasattr(model.type, 'value') else model.type,
            amount=model.amount,
            status=model.status,
            created_at=model.created_at,
            updated_at=model.updated_at,
            is_deleted=getattr(model, 'is_deleted', False)
        )

@dataclass(kw_only=True)
class DiscountCreateDTO:
    code: str
    amount: float
    discount_type: Optional[str] = "PERCENTAGE"
    description: Optional[str] = None
    min_order_value: Optional[float] = 0.0
    max_discount_value: Optional[float] = None
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None
    usage_limit: Optional[int] = None
    is_active: Optional[bool] = True

@dataclass(kw_only=True)
class DiscountUpdateDTO:
    description: Optional[str] = None
    is_active: Optional[bool] = None
    valid_to: Optional[datetime] = None

@dataclass(kw_only=True)
class DiscountResponseDTO(BaseDTO):
    id: str
    code: str
    description: Optional[str]
    discount_type: str
    amount: float
    min_order_value: float
    max_discount_value: Optional[float]
    valid_from: Optional[datetime]
    valid_to: Optional[datetime]
    usage_limit: Optional[int]
    times_used: int
    is_active: bool
    
    @classmethod
    def from_model(cls, model: object) -> 'DiscountResponseDTO':
        return cls(
            id=str(model.id),
            code=model.code,
            description=model.description,
            discount_type=model.discount_type.value if hasattr(model.discount_type, 'value') else model.discount_type,
            amount=model.amount,
            min_order_value=model.min_order_value,
            max_discount_value=model.max_discount_value,
            valid_from=model.valid_from,
            valid_to=model.valid_to,
            usage_limit=model.usage_limit,
            times_used=model.times_used,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
            is_deleted=getattr(model, 'is_deleted', False)
        )

@dataclass(kw_only=True)
class RefundCreateDTO:
    payment_id: str
    amount: float
    status: RefundStatus = RefundStatus.PENDING
    reason: Optional[str] = None
    processed_by: Optional[str] = None
    processor_refund_id: Optional[str] = None
    refund_date: Optional[datetime] = None

@dataclass(kw_only=True)
class RefundUpdateDTO:
    status: Optional[str] = None

@dataclass(kw_only=True)
class RefundResponseDTO(BaseDTO):
    id: str
    payment_id: str
    amount: float
    reason: Optional[str]
    status: str
    processed_by: Optional[str]
    processor_refund_id: Optional[str]
    refund_date: Optional[datetime]
    
    @classmethod
    def from_model(cls, model: object) -> 'RefundResponseDTO':
        return cls(
            id=str(model.id),
            payment_id=model.payment_id,
            amount=model.amount,
            reason=model.reason,
            status=model.status.value if hasattr(model.status, 'value') else model.status,
            processed_by=model.processed_by,
            processor_refund_id=model.processor_refund_id,
            refund_date=model.refund_date,
            created_at=model.created_at,
            updated_at=model.updated_at,
            is_deleted=getattr(model, 'is_deleted', False)
        )
