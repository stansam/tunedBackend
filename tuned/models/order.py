from tuned.extensions import db
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from tuned.models.user import User
from tuned.models.price import PriceRate
from tuned.models.service import Service
from tuned.models.order_delivery import OrderDelivery, OrderDeliveryFile
from tuned.models.enums import OrderStatus, SupportTicketStatus
from sqlalchemy import event
from sqlalchemy.orm import validates
from tuned.utils.orders import generate_public_order_number


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(20), unique=True, nullable=False, index=True)
    client_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=False)
    academic_level_id = db.Column(db.Integer, db.ForeignKey('academic_level.id'), nullable=False)
    deadline_id = db.Column(db.Integer, db.ForeignKey('deadline.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    word_count = db.Column(db.Integer, nullable=False)
    page_count = db.Column(db.Float, nullable=False)
    format_style = db.Column(db.String(50), nullable=True, default=None)
    report_type = db.Column(db.String(50), nullable=True, default=None)
    total_price = db.Column(db.Float, nullable=False)
    status = db.Column(db.Enum(OrderStatus), default=OrderStatus.PENDING, nullable=False)
    paid = db.Column(db.Boolean, default=False)
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)  # Soft delete support
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    delivered_at = db.Column(db.DateTime, nullable=True, default=None)
    extension_requested = db.Column(db.Boolean, default=False)
    extension_requested_at = db.Column(db.DateTime, nullable=True, default=None)
    due_date = db.Column(db.DateTime, nullable=True, default=None)
    writer_is_assigned = db.Column(db.Boolean, default=False)
    writer_assigned_at = db.Column(db.DateTime)
    price_per_page = db.Column(db.Float, nullable=False)
    subtotal = db.Column(db.Float, nullable=False)
    discount_amount = db.Column(db.Float, nullable=True, default=0)
    currency = db.Column(db.Enum('Currency'), default='USD')
    additional_materials = db.Column(db.Text, nullable=True, default=None)
    
    # Relationships
    client = db.relationship('User', back_populates='orders')
    service = db.relationship('Service', back_populates='orders')
    academic_level = db.relationship('AcademicLevel', back_populates='orders')
    deadline = db.relationship('Deadline', back_populates='orders')
    testimonials = db.relationship('Testimonial', backref='order', lazy=True, cascade='all, delete-orphan')
    files = db.relationship('OrderFile', backref='order', lazy=True, cascade='all, delete-orphan')
    payments = db.relationship('Payment', back_populates='order', lazy=True, cascade='all, delete-orphan')
    invoice = db.relationship('Invoice', back_populates='order', uselist=False, cascade='all, delete-orphan')
    comments = db.relationship('OrderComment', backref='order', lazy=True, cascade="all, delete-orphan")
    deliveries = db.relationship('OrderDelivery', backref='order', lazy=True, cascade="all, delete-orphan")
    
    # Table arguments for indexes and constraints
    __table_args__ = (
        db.Index('ix_order_client_status_created', 'client_id', 'status', 'created_at'),
        db.CheckConstraint('word_count > 0', name='valid_word_count'),
        db.CheckConstraint('page_count > 0', name='valid_page_count'),
        db.CheckConstraint('total_price > 0', name='valid_total_price'),
    )
    
    # Valid state transitions for order status
    VALID_STATUS_TRANSITIONS = {
        OrderStatus.PENDING: [OrderStatus.ACTIVE, OrderStatus.CANCELED],
        OrderStatus.ACTIVE: [OrderStatus.COMPLETED_PENDING_REVIEW, OrderStatus.OVERDUE, OrderStatus.CANCELED],
        OrderStatus.COMPLETED_PENDING_REVIEW: [OrderStatus.COMPLETED, OrderStatus.REVISION],
        OrderStatus.REVISION: [OrderStatus.ACTIVE, OrderStatus.COMPLETED_PENDING_REVIEW],
        OrderStatus.OVERDUE: [OrderStatus.ACTIVE, OrderStatus.CANCELED],
        OrderStatus.COMPLETED: [OrderStatus.REVISION],  # Allow revision after completion
        OrderStatus.CANCELED: [],  # Cannot transition from canceled
    }
    
    @validates('status')
    def validate_status_transition(self, key, new_status):
        """
        Validate order status transitions using state machine logic.
        
        Args:
            key: Attribute name ('status')
            new_status: New status to transition to
            
        Returns:
            OrderStatus: Validated new status
            
        Raises:
            ValueError: If transition is invalid
        """
        # Allow initial status setting (when object is new)
        if not self.id or not hasattr(self, '_sa_instance_state') or self._sa_instance_state.key is None:
            return new_status
        
        current_status = self.status
        
        # If status hasn't changed, allow it
        if current_status == new_status:
            return new_status
        
        # Check if transition is valid
        valid_transitions = self.VALID_STATUS_TRANSITIONS.get(current_status, [])
        
        if new_status not in valid_transitions:
            raise ValueError(
                f'Invalid status transition from {current_status.value} to {new_status.value}. '
                f'Valid transitions: {[s.value for s in valid_transitions]}'
            )
        
        return new_status
    
    @property
    def status_color(self):
        colors = {
            OrderStatus.PENDING: 'secondary',
            OrderStatus.ACTIVE: 'primary',
            OrderStatus.COMPLETED_PENDING_REVIEW: 'success',
            OrderStatus.COMPLETED: 'success',
            OrderStatus.OVERDUE: 'danger',
            OrderStatus.CANCELED: 'dark',
            OrderStatus.REVISION: 'info',
        }
        return colors.get(self.status, 'warning')
    
    @property
    def latest_delivery(self):
        """Get the most recent delivery for this order"""
        return OrderDelivery.query.filter_by(order_id=self.id).order_by(OrderDelivery.delivered_at.desc()).first()

    @property
    def is_delivered(self):
        """Check if order has been delivered"""
        return self.latest_delivery is not None
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.order_number = self.generate_order_number()
    
       
    def __repr__(self):
        return f'<Order {self.order_number}>'

class OrderSequence(db.Model):
    __tablename__ = "order_sequences"

    year = db.Column(db.Integer, primary_key=True)
    month = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.Integer, nullable=False, default=0)
    
class OrderFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    # file_category = db.Column(db.String(255), nullable=False)
    # file_type = db.Column(db.String(255), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    is_from_client = db.Column(db.Boolean, default=True)
    
    @property
    def file_size(self):
        """
        Return size in bytes of the file on disk, or 0 if missing.
        """
        import os
        try:
            return os.path.getsize(self.file_path)
        except (OSError, TypeError):
            return 0
    
    # @property
    # def is_from_client(self):
    #     user = User.query.get(self.uploaded_by)
    #     return not user.is_admin
    
    def __repr__(self):
        return f'<OrderFile {self.filename}>'

class OrderComment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    message = db.Column(db.Text)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    is_read = db.Column(db.Boolean, default=False)
    
    # Relationship
    user = db.relationship('User', backref='order_comments')
    
    def __repr__(self):
        return f'<OrderComment {self.id}>'


class SupportTicket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subject = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.Enum(SupportTicketStatus), default=SupportTicketStatus.OPEN, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    order = db.relationship('Order', backref='support_tickets')
    user = db.relationship('User', backref='support_tickets')
    
    def __repr__(self):
        return f'<SupportTicket {self.id} for Order {self.order_id}>'


@event.listens_for(Order, "before_insert")
def set_public_order_number(mapper, connection, target):
    if target.order_number:
        return

    target.order_number = generate_public_order_number(connection)