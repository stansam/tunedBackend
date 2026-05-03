from tuned.models.base import BaseModel
from datetime import datetime, timezone
from tuned.extensions import db
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, TYPE_CHECKING, Any
from tuned.models.enums import OrderStatus, EmailStatus

if TYPE_CHECKING:
    from tuned.models.price import PriceRate
    from tuned.models.order import Order
    from tuned.models.user import User

class PriceHistory(BaseModel):
    __tablename__ = 'price_history'
    
    price_rate_id: Mapped[str] = mapped_column(db.String(36), db.ForeignKey('price_rate.id'), nullable=False, index=True)
    old_price: Mapped[float] = mapped_column(db.Numeric(precision=10, scale=2), nullable=False)
    new_price: Mapped[float] = mapped_column(db.Numeric(precision=10, scale=2), nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    
    __table_args__ = (
        db.Index('ix_price_history_rate_date', 'price_rate_id', 'updated_at'),
    )
    
    price_rate: Mapped["PriceRate"] = relationship('PriceRate', foreign_keys=[price_rate_id], back_populates='price_history')
    
    def __repr__(self) -> str:
        return f'<PriceHistory PriceRate:{self.price_rate_id} ${self.old_price}→${self.new_price}>'


class OrderStatusHistory(BaseModel):
    __tablename__ = 'order_status_history'
    
    order_id: Mapped[str] = mapped_column(db.String(36), db.ForeignKey('order.id'), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(db.String(36), db.ForeignKey('users.id'), nullable=False, index=True)
    old_status: Mapped[Optional[OrderStatus]] = mapped_column(db.Enum(OrderStatus), nullable=True)
    new_status: Mapped[OrderStatus] = mapped_column(db.Enum(OrderStatus), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(db.String(45), nullable=True)
    
    __table_args__ = (
        db.Index('ix_status_history_order_date', 'order_id', 'updated_at'),
    )
    
    order: Mapped["Order"] = relationship('Order', foreign_keys=[order_id], back_populates='status_history')
    
    def __repr__(self) -> str:
        return f'<OrderStatusHistory Order:{self.order_id} {self.old_status}→{self.new_status}>'


class ActivityLog(BaseModel):
    __tablename__ = 'activity_log'
    
    user_id: Mapped[Optional[str]] = mapped_column(db.String(36), db.ForeignKey('users.id'), nullable=True, index=True)
    action: Mapped[str] = mapped_column(db.String(100), nullable=False, index=True)  # e.g., "order_created", "payment_received"
    entity_type: Mapped[Optional[str]] = mapped_column(db.String(50), nullable=True, index=True)  # e.g., "Order", "Payment", "User"
    entity_id: Mapped[Optional[str]] = mapped_column(db.String(36), nullable=True, index=True)
    before: Mapped[Optional[dict[str, Any]]] = mapped_column(db.JSON, nullable=True)
    after: Mapped[Optional[dict[str, Any]]] = mapped_column(db.JSON, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(db.String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)
    
    __table_args__ = (
        db.Index('ix_activity_log_user_date', 'user_id', 'created_at'),
        db.Index('ix_activity_log_entity', 'entity_type', 'entity_id'),
        db.Index('ix_activity_log_action_date', 'action', 'created_at'),
    )
    
    user: Mapped[Optional["User"]] = relationship('User', foreign_keys=[user_id], back_populates='activity_logs')
    
    def __repr__(self) -> str:
        return f'<ActivityLog {self.action} by User:{self.user_id}>'


class EmailLog(BaseModel):
    __tablename__ = 'email_log'
    
    recipient: Mapped[str] = mapped_column(db.String(120), nullable=False, index=True)
    subject: Mapped[str] = mapped_column(db.String(255), nullable=False)
    template: Mapped[Optional[str]] = mapped_column(db.String(100), nullable=True)  # Email template name used
    status: Mapped[EmailStatus] = mapped_column(db.Enum(EmailStatus), default=EmailStatus.PENDING, nullable=False, index=True)  # pending, sent, failed
    error_message: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    sent_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True)
    
    user_id: Mapped[Optional[str]] = mapped_column(db.String(36), db.ForeignKey('users.id'), nullable=True, index=True)
    order_id: Mapped[Optional[str]] = mapped_column(db.String(36), db.ForeignKey('order.id'), nullable=True, index=True)
    
    __table_args__ = (
        db.Index('ix_email_log_status_date', 'status', 'created_at'),
        db.Index('ix_email_log_recipient_date', 'recipient', 'created_at'),
    )
    
    user: Mapped[Optional["User"]] = relationship('User', foreign_keys=[user_id], back_populates='email_logs')
    order: Mapped[Optional["Order"]] = relationship('Order', foreign_keys=[order_id], back_populates='email_logs')
    
    @staticmethod
    def log_email(recipient: str, subject: str, template: Optional[str]=None, user_id: Optional[str]=None, order_id: Optional[str]=None) -> "EmailLog":
        email_log = EmailLog(
            recipient=recipient,
            subject=subject,
            template=template,
            user_id=user_id,
            order_id=order_id
        )
        db.session.add(email_log)
        db.session.commit()
        return email_log
    
    def mark_sent(self) -> None:
        self.status = EmailStatus.SENT
        self.sent_at = datetime.now(timezone.utc)
        db.session.commit()
    
    def mark_failed(self, error_message: str) -> None:
        self.status = EmailStatus.FAILED
        self.error_message = error_message
        db.session.commit()
    
    def __repr__(self) -> str:
        return f'<EmailLog to:{self.recipient} status:{self.status}>'
