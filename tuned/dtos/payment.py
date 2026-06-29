from tuned.models.enums import (
    RefundStatus, PaymentStatus, MethodCategory, TransactionType,
    TransactionStatus, DiscountType, Currency
)
from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING
from datetime import datetime
from tuned.dtos.base import BaseDTO

if TYPE_CHECKING:
    from tuned.models.payment import AcceptedPaymentMethod, Payment, Invoice, Transaction, Discount, Refund


@dataclass(kw_only=True)
class AcceptedMethodCreateDTO:
    name: str
    category: MethodCategory
    details: Optional[str] = None
    is_active: Optional[bool] = True

@dataclass(kw_only=True)
class AcceptedMethodUpdateDTO:
    name: Optional[str] = None
    category: Optional[MethodCategory] = None
    details: Optional[str] = None
    is_active: Optional[bool] = None

@dataclass(kw_only=True)
class AcceptedMethodResponseDTO(BaseDTO):
    id: str
    name: str
    category: MethodCategory
    details: Optional[str]
    is_active: bool

    @classmethod
    def from_model(cls, model: "AcceptedPaymentMethod") -> 'AcceptedMethodResponseDTO':
        return cls(
            id=str(model.id),
            name=model.name,
            category=model.category,
            details=model.details,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
            is_deleted=getattr(model, 'is_deleted', False)
        )

@dataclass(kw_only=True)
class PaymentCreateDTO:
    order_id: str
    user_id: str
    amount: float
    accepted_method_id: str
    status: PaymentStatus = PaymentStatus.PENDING

@dataclass(kw_only=True)
class PaymentClientMarkDTO:
    client_proof_reference: str

@dataclass(kw_only=True)
class PaymentAdminVerifyDTO:
    admin_notes: Optional[str] = None

@dataclass(kw_only=True)
class PaymentUpdateDTO:
    status: Optional[PaymentStatus] = None
    client_proof_reference: Optional[str] = None
    pesapal_tracking_id: Optional[str] = None
    admin_notes: Optional[str] = None
    client_marked_paid_at: Optional[datetime] = None
    admin_verified_at: Optional[datetime] = None

@dataclass(kw_only=True)
class PaymentResponseDTO(BaseDTO):
    id: str
    payment_id: str
    order_id: str
    user_id: str
    amount: float
    status: str
    accepted_method_id: str
    currency: str
    client_proof_reference: Optional[str]
    pesapal_tracking_id: Optional[str]
    admin_notes: Optional[str]
    client_marked_paid_at: Optional[datetime]
    admin_verified_at: Optional[datetime]
    
    @classmethod
    def from_model(cls, model: "Payment") -> 'PaymentResponseDTO':
        return cls(
            id=str(model.id),
            payment_id=model.payment_id,
            order_id=str(model.order_id),
            user_id=str(model.user_id),
            amount=float(model.amount),
            status=model.status.value,
            accepted_method_id=str(model.accepted_method_id),
            currency=model.currency.value,
            client_proof_reference=model.client_proof_reference,
            pesapal_tracking_id=getattr(model, 'pesapal_tracking_id', None),
            admin_notes=getattr(model, 'admin_notes', None),
            client_marked_paid_at=model.client_marked_paid_at,
            admin_verified_at=model.admin_verified_at,
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
    def from_model(cls, model: "Invoice") -> 'InvoiceResponseDTO':
        return cls(
            id=str(model.id),
            invoice_number=model.invoice_number,
            order_id=str(model.order_id),
            user_id=str(model.user_id),
            payment_id=str(model.payment_id) if model.payment_id else None,
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
    type: TransactionType
    amount: float
    status: TransactionStatus
    reference: Optional[str] = None

@dataclass(kw_only=True)
class TransactionResponseDTO(BaseDTO):
    id: str
    transaction_id: str
    payment_id: str
    type: TransactionType
    amount: float
    status: TransactionStatus
    reference: Optional[str]
    
    @classmethod
    def from_model(cls, model: "Transaction") -> 'TransactionResponseDTO':
        return cls(
            id=str(model.id),
            transaction_id=model.transaction_id,
            payment_id=str(model.payment_id),
            type=model.type,
            amount=float(model.amount),
            status=model.status,
            reference=getattr(model, 'reference', None),
            created_at=model.created_at,
            updated_at=model.updated_at,
            is_deleted=getattr(model, 'is_deleted', False)
        )

@dataclass(kw_only=True)
class DiscountCreateDTO:
    code: str
    amount: float
    discount_type: DiscountType = DiscountType.PERCENTAGE
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
    discount_type: DiscountType
    amount: float
    min_order_value: float
    max_discount_value: Optional[float]
    valid_from: Optional[datetime]
    valid_to: Optional[datetime]
    usage_limit: Optional[int]
    times_used: int
    is_active: bool
    
    @classmethod
    def from_model(cls, model: "Discount") -> 'DiscountResponseDTO':
        return cls(
            id=str(model.id),
            code=model.code,
            description=model.description,
            discount_type=model.discount_type,
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
    admin_reference_id: Optional[str] = None
    refund_date: Optional[datetime] = None

@dataclass(kw_only=True)
class RefundUpdateDTO:
    status: Optional[RefundStatus] = None

@dataclass(kw_only=True)
class RefundResponseDTO(BaseDTO):
    id: str
    payment_id: Optional[str]
    amount: float
    reason: Optional[str]
    status: RefundStatus
    processed_by: Optional[str]
    admin_reference_id: Optional[str]
    refund_date: Optional[datetime]
    
    @classmethod
    def from_model(cls, model: "Refund") -> 'RefundResponseDTO':
        return cls(
            id=str(model.id),
            payment_id=str(model.payment_id) if model.payment_id else None,
            amount=model.amount,
            reason=model.reason,
            status=model.status,
            processed_by=str(model.processed_by) if model.processed_by else None,
            admin_reference_id=str(model.admin_reference_id) if model.admin_reference_id else None,
            refund_date=model.refund_date,
            created_at=model.created_at,
            updated_at=model.updated_at,
            is_deleted=getattr(model, 'is_deleted', False)
        )

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
class PaymentListRequestDTO:
    status: Optional[str] = None
    page: Optional[int] = 1
    per_page: Optional[int] = 10

@dataclass
class PaymentListResponseDTO:
    payments: list[PaymentResponseDTO]
    total: int
    page: int
    per_page: int

@dataclass(kw_only=True)
class PesapalSubmitOrderDTO:
    merchant_reference: str
    amount: float
    currency: str
    email: str
    phone: str
    first_name: str
    last_name: str
    description: str

@dataclass(kw_only=True)
class PesapalSubmitOrderResponseDTO:
    redirect_url: str
    order_tracking_id: str
    merchant_reference: str

@dataclass(kw_only=True)
class PesapalTransactionStatusDTO:
    payment_status_description: str
    amount: float
    currency: str
    payment_method: Optional[str]
    order_tracking_id: str
    merchant_reference: str

@dataclass(kw_only=True)
class PaymentStatusResponseDTO:
    payment_id: str
    internal_id: str
    status: PaymentStatus
    order_id: str
    is_completed: bool

@dataclass(kw_only=True)
class AcceptedMethodAdminResponseDTO(BaseDTO):
    id: str
    name: str
    category: MethodCategory
    details: Optional[str]
    is_active: bool
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    @classmethod
    def from_model(cls, model: "AcceptedPaymentMethod") -> "AcceptedMethodAdminResponseDTO":
        return cls(
            id=str(model.id),
            name=model.name,
            category=model.category,
            details=model.details,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
            is_deleted=getattr(model, 'is_deleted', False)
        )


@dataclass(kw_only=True)
class AdminPaymentResponseDTO(PaymentResponseDTO):
    client_name: str
    client_email: str
    order_number: str
    payment_method_name: str
    payment_method_category: str

    @classmethod
    def from_model_and_relations(
        cls,
        model: "Payment",
        client_name: str,
        client_email: str,
        order_number: str,
        payment_method_name: str,
        payment_method_category: str
    ) -> "AdminPaymentResponseDTO":
        return cls(
            id=str(model.id),
            payment_id=model.payment_id,
            order_id=str(model.order_id),
            user_id=str(model.user_id),
            amount=float(model.amount),
            status=model.status,
            accepted_method_id=str(model.accepted_method_id),
            currency=model.currency,
            client_proof_reference=model.client_proof_reference,
            pesapal_tracking_id=getattr(model, 'pesapal_tracking_id', None),
            admin_notes=getattr(model, 'admin_notes', None),
            client_marked_paid_at=model.client_marked_paid_at,
            admin_verified_at=model.admin_verified_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
            is_deleted=getattr(model, 'is_deleted', False),
            client_name=client_name,
            client_email=client_email,
            order_number=order_number,
            payment_method_name=payment_method_name,
            payment_method_category=payment_method_category
        )


@dataclass
class AdminPaymentListRequestDTO:
    status: Optional[str] = None
    q: Optional[str] = None
    page: int = 1
    per_page: int = 10


@dataclass
class AdminPaymentListResponseDTO:
    payments: list[AdminPaymentResponseDTO]
    total: int
    page: int
    per_page: int


