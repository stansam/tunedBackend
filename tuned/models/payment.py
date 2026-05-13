from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, ENUM
from sqlalchemy.sql import func
from typing import TYPE_CHECKING, Optional, Any
from datetime import datetime, timezone
import uuid
from tuned.extensions import db
from tuned.models.base import BaseModel
from tuned.models.enums import(
    PaymentStatus, MethodCategory, TransactionType,
    RefundStatus, DiscountType, Currency, TransactionStatus
)

if TYPE_CHECKING:
    from tuned.models.order import Order
    from tuned.models.user import User

class AcceptedPaymentMethod(BaseModel):
    __tablename__ = 'accepted_payment_method'
    name: Mapped[str] = mapped_column(db.String(100), nullable=False)
    category: Mapped[MethodCategory] = mapped_column(ENUM(MethodCategory, name="methodcategory"), nullable=False)
    details: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(db.Boolean, default=True, nullable=False)

    def __init__(self, name: str, category: MethodCategory, details: Optional[str]=None, is_active: bool=True) -> None:
        self.name = name
        self.category = category
        self.details = details
        self.is_active = is_active

    def __repr__(self) -> str:
        return f"<AcceptedPaymentMethod {self.name}>"

class Payment(BaseModel):
    __tablename__ = 'payment'
    payment_id: Mapped[str] = mapped_column(db.String(36), unique=True, nullable=False)
    order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), db.ForeignKey('order.id'), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False, index=True)
    accepted_method_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), db.ForeignKey('accepted_payment_method.id'), nullable=False, index=True)
    currency: Mapped[Currency] = mapped_column(ENUM(Currency, name="currency"), default=Currency.USD, nullable=False)
    amount: Mapped[float] = mapped_column(db.Numeric(precision=10, scale=2), nullable=False)
    status: Mapped[PaymentStatus] = mapped_column(ENUM(PaymentStatus, name="paymentstatus"), default=PaymentStatus.PENDING, nullable=False, index=True)
    
    client_proof_reference: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)
    client_marked_paid_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime(timezone=True), nullable=True)
    admin_verified_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime(timezone=True), nullable=True)
    
    order: Mapped["Order"] = relationship('Order', foreign_keys=[order_id], back_populates='payments')
    user: Mapped["User"] = relationship('User', foreign_keys=[user_id], back_populates='payments')
    accepted_method: Mapped["AcceptedPaymentMethod"] = relationship('AcceptedPaymentMethod', foreign_keys=[accepted_method_id])
    transactions: Mapped[list["Transaction"]] = relationship('Transaction', foreign_keys='Transaction.payment_id', back_populates='payment', lazy=True)
    invoice: Mapped[Optional["Invoice"]] = relationship('Invoice', foreign_keys='Invoice.payment_id', back_populates='payment', uselist=False)
    refunds: Mapped[list["Refund"]] = relationship('Refund', foreign_keys="Refund.payment_id", back_populates='payment')
    
    __table_args__ = (
        db.Index('ix_payment_order_status', 'order_id', 'status'),
        db.CheckConstraint('amount > 0', name='valid_payment_amount'),
    )

    def __init__(self, order_id: uuid.UUID, user_id: uuid.UUID, amount: float, accepted_method_id: uuid.UUID, status: PaymentStatus=PaymentStatus.PENDING) -> None:
        self.payment_id = f"PAY-{uuid.uuid4().hex[:12].upper()}"
        self.order_id = order_id
        self.user_id = user_id
        self.amount = amount
        self.accepted_method_id = accepted_method_id
        self.status = status
    
    def __repr__(self) -> str:
        return f"Payment {self.payment_id} for Order {self.order_id}"

class Invoice(BaseModel):
    __tablename__ = 'invoice'
    invoice_number: Mapped[str] = mapped_column(db.String(20), unique=True, nullable=False)
    order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), db.ForeignKey('order.id'), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False, index=True)
    payment_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), db.ForeignKey('payment.id'), nullable=True, index=True)
    
    subtotal: Mapped[float] = mapped_column(db.Numeric(precision=10, scale=2), nullable=False)
    discount: Mapped[float] = mapped_column(db.Numeric(precision=10, scale=2), default=0, nullable=False)
    tax: Mapped[float] = mapped_column(db.Numeric(precision=10, scale=2), default=0, nullable=False)
    total: Mapped[float] = mapped_column(db.Numeric(precision=10, scale=2), nullable=False)
    due_date: Mapped[datetime] = mapped_column(db.DateTime(timezone=True), nullable=False)
    paid: Mapped[bool] = mapped_column(db.Boolean, default=False, nullable=False, index=True)
    
    order: Mapped["Order"] = relationship('Order', foreign_keys=[order_id], back_populates='invoice')
    user: Mapped["User"] = relationship('User', foreign_keys=[user_id], back_populates='invoices')
    payment: Mapped[Optional["Payment"]] = relationship('Payment', foreign_keys=[payment_id], back_populates='invoice')
    
    def __init__(self, order_id: uuid.UUID, user_id: uuid.UUID, subtotal: float, total: float, due_date: datetime, payment_id: Optional[uuid.UUID]=None, discount: float=0, tax: float=0, paid: bool=False) -> None:
        year_month = datetime.now(timezone.utc).strftime('%Y%m')
        
        count = Invoice.query.filter(
            func.strftime('%Y%m', Invoice.created_at) == year_month
        ).count() + 1
        
        self.invoice_number = f"INV-{year_month}-{count:04d}"
        self.order_id = order_id
        self.user_id = user_id
        self.payment_id = payment_id
        self.subtotal = subtotal
        self.discount = discount
        self.tax = tax
        self.total = total
        self.due_date = due_date
        self.paid = paid
    
    def __repr__(self) -> str:
        return f"Invoice {self.invoice_number}"

class Transaction(BaseModel):
    __tablename__ = 'transaction'
    # transaction_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), unique=True, nullable=False, index=True)
    payment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), db.ForeignKey('payment.id'), nullable=False, index=True)
    type: Mapped[TransactionType] = mapped_column(ENUM(TransactionType, name="transactiontype"), nullable=False, index=True)
    amount: Mapped[float] = mapped_column(db.Numeric(precision=10, scale=2), nullable=False)
    status: Mapped[TransactionStatus] = mapped_column(ENUM(TransactionStatus, name="transactionstatus"), nullable=False, index=True)

    __table_args__ = (
        db.CheckConstraint('amount > 0', name='valid_transaction_amount'),
    )

    payment: Mapped["Payment"] = relationship('Payment', back_populates='transactions')
    
    def __init__(self, payment_id: uuid.UUID, type: TransactionType, amount: float, status: TransactionStatus) -> None:
        self.payment_id = payment_id
        # self.transaction_id = transaction_id
        self.type = type
        self.amount = amount
        self.status = status
    
    def __repr__(self) -> str:
        return f"{self.type.title()} of {self.amount} for Payment #{self.payment_id}"
    
class Discount(BaseModel):
    __tablename__ = 'discount'
    code: Mapped[str] = mapped_column(db.String(20), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(db.String(200), nullable=True)
    discount_type: Mapped[DiscountType] = mapped_column(ENUM(DiscountType, name="discounttype"), default=DiscountType.PERCENTAGE, nullable=False)
    amount: Mapped[float] = mapped_column(db.Numeric(precision=10, scale=2), nullable=False)
    min_order_value: Mapped[float] = mapped_column(db.Numeric(precision=10, scale=2), default=0, nullable=False)
    max_discount_value: Mapped[Optional[float]] = mapped_column(db.Numeric(precision=10, scale=2), nullable=True)
    valid_from: Mapped[datetime] = mapped_column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    valid_to: Mapped[Optional[datetime]] = mapped_column(db.DateTime(timezone=True), nullable=True)
    usage_limit: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True)
    times_used: Mapped[int] = mapped_column(db.Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(db.Boolean, default=True, nullable=False, index=True)
    
    orders: Mapped[list["Order"]] = relationship('Order', secondary='order_discount', back_populates='discounts')
    
    __table_args__ = (
        db.CheckConstraint('amount > 0', name='valid_discount_amount'),
        db.CheckConstraint('min_order_value >= 0', name='valid_min_order'),
    )
    
    def __init__(self, **kwargs: Any) -> None:
        super(Discount, self).__init__(**kwargs)
        
    def __repr__(self) -> str:
        return f'<Discount {self.code}>'


order_discount = db.Table('order_discount',
    db.Column('order_id', UUID(as_uuid=True), db.ForeignKey('order.id'), primary_key=True),
    db.Column('discount_id', UUID(as_uuid=True), db.ForeignKey('discount.id'), primary_key=True)
)

class Refund(BaseModel):
    __tablename__ = 'refund'
    payment_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), db.ForeignKey('payment.id'), nullable=True, index=True)
    amount: Mapped[float] = mapped_column(db.Numeric(precision=10, scale=2), nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    status: Mapped[RefundStatus] = mapped_column(ENUM(RefundStatus, name="refundstatus"), default=RefundStatus.PENDING, nullable=False, index=True)
    processed_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=True, index=True)
    refund_date: Mapped[Optional[datetime]] = mapped_column(db.DateTime(timezone=True), nullable=True)
    admin_reference_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    
    payment: Mapped[Optional["Payment"]] = relationship('Payment', foreign_keys=[payment_id], back_populates='refunds')
    admin: Mapped[Optional["User"]] = relationship('User', foreign_keys=[processed_by], back_populates='processed_refunds')
    
    __table_args__ = (
        db.CheckConstraint('amount > 0', name='valid_refund_amount'),
    )

    def __init__(self, **kwargs: Any) -> None:
        super(Refund, self).__init__(**kwargs)

    def __repr__(self) -> str:
        return f'<Refund {self.id}>'