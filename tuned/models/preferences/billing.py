
from tuned.extensions import db
from tuned.models.enums import InvoiceDeliveryMethod
from tuned.models.base import BaseModel

class UserBillingPreferences(BaseModel):
    __tablename__ = 'user_billing_preferences'
    
    user_id = db.Column(
        db.String(36),
        db.ForeignKey('users.id', ondelete='CASCADE'),
        unique=True,
        nullable=False,
        index=True
    )
    
    invoice_email = db.Column(db.String(120), nullable=True)
    invoice_delivery = db.Column(
        db.Enum(InvoiceDeliveryMethod),
        default=InvoiceDeliveryMethod.EMAIL,
        nullable=False
    )
    
    payment_reminders = db.Column(db.Boolean, default=True, nullable=False)
    reminder_days_before = db.Column(db.Integer, default=3, nullable=False)
    
    auto_reload_enabled = db.Column(db.Boolean, default=False, nullable=True)
    auto_reload_threshold = db.Column(db.Numeric(10, 2), nullable=True)
    
    user = db.relationship('User', foreign_keys=[user_id], backref=db.backref('billing_preferences', uselist=False, lazy=True))
    
    def to_dict(self):
        return {
            'invoice_email': self.invoice_email,
            'invoice_delivery': self.invoice_delivery.value if self.invoice_delivery else 'email',
            'payment_reminders': self.payment_reminders,
            'reminder_days_before': self.reminder_days_before,
            'auto_reload_enabled': self.auto_reload_enabled,
            'auto_reload_threshold': float(self.auto_reload_threshold) if self.auto_reload_threshold else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<UserBillingPreferences user_id={self.user_id}>'
