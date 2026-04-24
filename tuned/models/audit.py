from tuned.models.base import BaseModel
from datetime import datetime, timezone
from tuned.extensions import db

class PriceHistory(BaseModel):
    __tablename__ = 'price_history'
    
    price_rate_id = db.Column(db.String(36), db.ForeignKey('price_rate.id'), nullable=False, index=True)
    old_price = db.Column(db.Numeric(precision=10, scale=2), nullable=False)
    new_price = db.Column(db.Numeric(precision=10, scale=2), nullable=False)
    reason = db.Column(db.Text)
    
    __table_args__ = (
        db.Index('ix_price_history_rate_date', 'price_rate_id', 'updated_at'),
    )
    
    price_rate = db.relationship('PriceRate', foreign_keys=[price_rate_id], backref='price_history')
    
    def __repr__(self):
        return f'<PriceHistory PriceRate:{self.price_rate_id} ${self.old_price}→${self.new_price}>'


class OrderStatusHistory(BaseModel):
    __tablename__ = 'order_status_history'
    
    order_id = db.Column(db.String(36), db.ForeignKey('order.id'), nullable=False, index=True)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, index=True)
    old_status = db.Column(db.String(50))
    new_status = db.Column(db.String(50), nullable=False)
    notes = db.Column(db.Text)
    ip_address = db.Column(db.String(45))  # IPv4 or IPv6
    
    __table_args__ = (
        db.Index('ix_status_history_order_date', 'order_id', 'updated_at'),
    )
    
    order = db.relationship('Order', foreign_keys=[order_id], backref='status_history')
    
    def __repr__(self):
        return f'<OrderStatusHistory Order:{self.order_id} {self.old_status}→{self.new_status}>'


class ActivityLog(BaseModel):
    __tablename__ = 'activity_log'
    
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), index=True)
    action = db.Column(db.String(100), nullable=False, index=True)  # e.g., "order_created", "payment_received"
    entity_type = db.Column(db.String(50), index=True)  # e.g., "Order", "Payment", "User"
    entity_id = db.Column(db.String(36), index=True)
    before = db.Column(db.JSON, nullable=True)
    after = db.Column(db.JSON, nullable=True)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(255))
    
    __table_args__ = (
        db.Index('ix_activity_log_user_date', 'user_id', 'created_at'),
        db.Index('ix_activity_log_entity', 'entity_type', 'entity_id'),
        db.Index('ix_activity_log_action_date', 'action', 'created_at'),
    )
    
    user = db.relationship('User', foreign_keys=[user_id], backref='activity_logs')
    
    def __repr__(self):
        return f'<ActivityLog {self.action} by User:{self.user_id}>'


class EmailLog(BaseModel):
    __tablename__ = 'email_log'
    
    recipient = db.Column(db.String(120), nullable=False, index=True)
    subject = db.Column(db.String(255), nullable=False)
    template = db.Column(db.String(100))  # Email template name used
    status = db.Column(db.String(20), default='pending', index=True)  # pending, sent, failed
    error_message = db.Column(db.Text)
    sent_at = db.Column(db.DateTime)
    
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), index=True)
    order_id = db.Column(db.String(36), db.ForeignKey('order.id'), index=True, nullable=True)
    
    __table_args__ = (
        db.Index('ix_email_log_status_date', 'status', 'created_at'),
        db.Index('ix_email_log_recipient_date', 'recipient', 'created_at'),
    )
    
    user = db.relationship('User', foreign_keys=[user_id], backref='email_logs')
    order = db.relationship('Order', foreign_keys=[order_id], backref='email_logs')
    
    @staticmethod
    def log_email(recipient, subject, template=None, user_id=None, order_id=None):
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
    
    def mark_sent(self):
        self.status = 'sent'
        self.sent_at = datetime.now(timezone.utc)
        db.session.commit()
    
    def mark_failed(self, error_message):
        self.status = 'failed'
        self.error_message = error_message
        db.session.commit()
    
    def __repr__(self):
        return f'<EmailLog to:{self.recipient} status:{self.status}>'
