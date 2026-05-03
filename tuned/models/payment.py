from tuned.extensions import db
from tuned.models.base import BaseModel
from datetime import datetime, timezone
import uuid
from sqlalchemy.sql import func
from tuned.models.enums import(
    PaymentStatus, MethodCategory, TransactionType,
    RefundStatus, DiscountType, Currency, TransactionStatus
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from tuned.models.order import Order
    from tuned.models.user import User

class AcceptedPaymentMethod(BaseModel):
    __tablename__ = 'accepted_payment_method'
    name: Mapped[str] = mapped_column(db.String(100), nullable=False)
    category: Mapped[MethodCategory] = mapped_column(db.Enum(MethodCategory), nullable=False)
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
    order_id: Mapped[str] = mapped_column(db.String(36), db.ForeignKey('order.id'), nullable=False)
    user_id: Mapped[str] = mapped_column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    accepted_method_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('accepted_payment_method.id'), nullable=False)
    currency: Mapped[Currency] = mapped_column(db.Enum(Currency), default=Currency.USD, nullable=False)
    amount: Mapped[float] = mapped_column(db.Float, nullable=False)
    status: Mapped[PaymentStatus] = mapped_column(db.Enum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)
    
    client_proof_reference: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)
    client_marked_paid_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True)
    admin_verified_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True)
    
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

    def __init__(self, order_id: str, user_id: str, amount: float, accepted_method_id: int, status: PaymentStatus=PaymentStatus.PENDING) -> None:
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
    order_id: Mapped[str] = mapped_column(db.String(36), db.ForeignKey('order.id'), nullable=False)
    user_id: Mapped[str] = mapped_column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    payment_id: Mapped[Optional[str]] = mapped_column(db.String(36), db.ForeignKey('payment.id'), nullable=True)
    
    subtotal: Mapped[float] = mapped_column(db.Float, nullable=False)
    discount: Mapped[float] = mapped_column(db.Float, default=0, nullable=False)
    tax: Mapped[float] = mapped_column(db.Float, default=0, nullable=False)
    total: Mapped[float] = mapped_column(db.Float, nullable=False)
    due_date: Mapped[datetime] = mapped_column(db.DateTime, nullable=False)
    paid: Mapped[bool] = mapped_column(db.Boolean, default=False, nullable=False)
    
    order: Mapped["Order"] = relationship('Order', foreign_keys=[order_id], back_populates='invoice')
    user: Mapped["User"] = relationship('User', foreign_keys=[user_id], back_populates='invoices')
    payment: Mapped[Optional["Payment"]] = relationship('Payment', foreign_keys=[payment_id], back_populates='invoice')
    
    def __init__(self, order_id: str, user_id: str, subtotal: float, total: float, due_date: datetime, payment_id: Optional[str]=None, discount: float=0, tax: float=0, paid: bool=False) -> None:
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
    transaction_id: Mapped[str] = mapped_column(db.String(100), unique=True, nullable=False)
    payment_id: Mapped[str] = mapped_column(db.String(36), db.ForeignKey('payment.id'), nullable=False)
    type: Mapped[TransactionType] = mapped_column(db.Enum(TransactionType), nullable=False)
    amount: Mapped[float] = mapped_column(db.Float, nullable=False)
    status: Mapped[TransactionStatus] = mapped_column(db.Enum(TransactionStatus), nullable=False)

    __table_args__ = (
        db.CheckConstraint('amount > 0', name='valid_transaction_amount'),
    )

    payment: Mapped["Payment"] = relationship('Payment', back_populates='transactions')
    
    def __init__(self, payment_id: str, transaction_id: str, type: TransactionType, amount: float, status: TransactionStatus) -> None:
        self.payment_id = payment_id
        self.transaction_id = transaction_id
        self.type = type
        self.amount = amount
        self.status = status
    
    def __repr__(self) -> str:
        return f"{self.type.title()} of {self.amount} for Payment #{self.payment_id}"
    
class Discount(BaseModel):
    __tablename__ = 'discount'
    code: Mapped[str] = mapped_column(db.String(20), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(db.String(200), nullable=True)
    discount_type: Mapped[DiscountType] = mapped_column(db.Enum(DiscountType), default=DiscountType.PERCENTAGE, nullable=False)
    amount: Mapped[float] = mapped_column(db.Float, nullable=False)
    min_order_value: Mapped[float] = mapped_column(db.Float, default=0, nullable=False)
    max_discount_value: Mapped[Optional[float]] = mapped_column(db.Float, nullable=True)
    valid_from: Mapped[datetime] = mapped_column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    valid_to: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True)
    usage_limit: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True)
    times_used: Mapped[int] = mapped_column(db.Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(db.Boolean, default=True, nullable=False)
    
    orders: Mapped[list["Order"]] = relationship('Order', secondary='order_discount', back_populates='discounts')
    
    __table_args__ = (
        db.CheckConstraint('amount > 0', name='valid_discount_amount'),
        db.CheckConstraint('min_order_value >= 0', name='valid_min_order'),
    )
    
    def __repr__(self) -> str:
        return f'<Discount {self.code}>'


order_discount = db.Table('order_discount',
    db.Column('order_id', db.String(36), db.ForeignKey('order.id'), primary_key=True),
    db.Column('discount_id', db.String(36), db.ForeignKey('discount.id'), primary_key=True)
)

class Refund(BaseModel):
    __tablename__ = 'refund'
    payment_id: Mapped[Optional[str]] = mapped_column(db.String(36), db.ForeignKey('payment.id'), nullable=True)
    amount: Mapped[float] = mapped_column(db.Float, nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    status: Mapped[RefundStatus] = mapped_column(db.Enum(RefundStatus), default=RefundStatus.PENDING, nullable=False)
    processed_by: Mapped[Optional[str]] = mapped_column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    refund_date: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True)
    admin_reference_id: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)
    
    payment: Mapped[Optional["Payment"]] = relationship('Payment', foreign_keys=[payment_id], back_populates='refunds')
    admin: Mapped[Optional["User"]] = relationship('User', foreign_keys=[processed_by], back_populates='processed_refunds')
    
    __table_args__ = (
        db.CheckConstraint('amount > 0', name='valid_refund_amount'),
    )
    
    def __repr__(self) -> str:
        return f'<Refund {self.id}>'