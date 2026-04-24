from tuned.extensions import db
from tuned.models.base import BaseModel
from datetime import datetime, timezone
import uuid
from sqlalchemy.sql import func
from tuned.models.enums import PaymentStatus, PaymentMethod, TransactionType, RefundStatus, DiscountType, Currency

class Payment(BaseModel):
    payment_id = db.Column(db.String(36), unique=True, nullable=False)
    order_id = db.Column(db.String(36), db.ForeignKey('order.id'), nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    currency = db.Column(db.Enum(Currency), default=Currency.USD, nullable=False)
    payment_method_token = db.Column(db.String(255))
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.Enum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)
    method = db.Column(db.Enum(PaymentMethod), nullable=False)
    
    
    processor_id = db.Column(db.String(255))
    processor_response = db.Column(db.Text)
    
    payer_id = db.Column(db.String(255))  
    approval_url = db.Column(db.String(500))
    
    order = db.relationship('Order', foreign_keys=[order_id], back_populates='payments')
    user = db.relationship('User', foreign_keys=[user_id], backref=db.backref('payments', lazy=True))
    transactions = db.relationship('Transaction', foreign_keys='Transaction.payment_id', backref='payment', lazy=True)
    invoice = db.relationship('Invoice', foreign_keys='Invoice.payment_id', back_populates='payment', uselist=False)
    
    __table_args__ = (
        db.Index('ix_payment_order_status', 'order_id', 'status'),
        db.CheckConstraint('amount > 0', name='valid_payment_amount'),
    )
    
    def __init__(self, order_id, user_id, amount, method, status='pending', processor_id=None, processor_response=None, payer_id=None):
        self.payment_id = f"PAY-{uuid.uuid4().hex[:12].upper()}"
        self.order_id = order_id
        self.user_id = user_id
        self.amount = amount
        self.status = status
        self.method = method
        self.processor_id = processor_id
        self.processor_response = processor_response
        self.payer_id = payer_id
    
    def __repr__(self):
        return f"Payment {self.payment_id} for Order {self.order_id}"

class Invoice(BaseModel):
    invoice_number = db.Column(db.String(20), unique=True, nullable=False)
    order_id = db.Column(db.String(36), db.ForeignKey('order.id'), nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    payment_id = db.Column(db.String(36), db.ForeignKey('payment.id'))
    
    subtotal = db.Column(db.Float, nullable=False)
    discount = db.Column(db.Float, default=0)
    tax = db.Column(db.Float, default=0)
    total = db.Column(db.Float, nullable=False)
    due_date = db.Column(db.DateTime, nullable=False)
    paid = db.Column(db.Boolean, default=False)
    
    order = db.relationship('Order', foreign_keys=[order_id], back_populates='invoice')
    user = db.relationship('User', foreign_keys=[user_id], backref=db.backref('invoices', lazy=True))
    payment = db.relationship('Payment', foreign_keys=[payment_id], back_populates='invoice')
    
    def __init__(self, order_id, user_id, subtotal, total, due_date, payment_id=None, discount=0, tax=0, paid=False):
        # INV-YYYYMM-NNNN
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
    
    def __repr__(self):
        return f"Invoice {self.invoice_number}"

class Transaction(BaseModel):
    transaction_id = db.Column(db.String(100), unique=True, nullable=False)
    payment_id = db.Column(db.String(36), db.ForeignKey('payment.id'), nullable=False)
    type = db.Column(db.Enum(TransactionType), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), nullable=False)
    
    processor_id = db.Column(db.String(255))
    processor_response = db.Column(db.Text)

    __table_args__ = (
        db.CheckConstraint('amount > 0', name='valid_transaction_amount'),
    )
    
    def __init__(self, payment_id, transaction_id, type, amount, status, processor_id=None, processor_response=None):
        self.payment_id = payment_id
        self.transaction_id = transaction_id
        self.type = type
        self.amount = amount
        self.status = status
        self.processor_id = processor_id
        self.processor_response = processor_response
    
    def __repr__(self):
        return f"{self.type.title()} of {self.amount} for Payment #{self.payment_id}"
    
class Discount(BaseModel):
    code = db.Column(db.String(20), unique=True, nullable=False)
    description = db.Column(db.String(200))
    discount_type = db.Column(db.Enum(DiscountType), default=DiscountType.PERCENTAGE, nullable=False)
    amount = db.Column(db.Float, nullable=False)  # percentage or fixed amount
    min_order_value = db.Column(db.Float, default=0)
    max_discount_value = db.Column(db.Float)
    valid_from = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    valid_to = db.Column(db.DateTime)
    usage_limit = db.Column(db.Integer)
    times_used = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    
    
    orders = db.relationship('Order', secondary='order_discount', backref='discounts')
    
    # Table arguments for constraints
    __table_args__ = (
        db.CheckConstraint('amount > 0', name='valid_discount_amount'),
        db.CheckConstraint('min_order_value >= 0', name='valid_min_order'),
    )
    
    def __repr__(self):
        return f'<Discount {self.code}>'


order_discount = db.Table('order_discount',
    db.Column('order_id', db.Integer, db.ForeignKey('order.id'), primary_key=True),
    db.Column('discount_id', db.Integer, db.ForeignKey('discount.id'), primary_key=True)
)

class Refund(BaseModel):
    payment_id = db.Column(db.String(36), db.ForeignKey('payment.id'))
    amount = db.Column(db.Float, nullable=False)
    reason = db.Column(db.Text)
    status = db.Column(db.Enum(RefundStatus), default=RefundStatus.PENDING, nullable=False)
    processed_by = db.Column(db.String(36), db.ForeignKey('users.id'))
    refund_date = db.Column(db.DateTime)
    
    processor_refund_id = db.Column(db.String(255))
    
    payment = db.relationship('Payment', foreign_keys=[payment_id], backref='refunds')
    admin = db.relationship('User', foreign_keys=[processed_by], backref='processed_refunds')
    
    __table_args__ = (
        db.CheckConstraint('amount > 0', name='valid_refund_amount'),
    )
    
    def __repr__(self):
        return f'<Refund {self.id}>'