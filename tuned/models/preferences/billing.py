"""
User billing preferences model.

This module defines the UserBillingPreferences model for storing
user billing and invoice preferences.
"""

from datetime import datetime, timezone
from tuned.extensions import db
from tuned.models.enums import InvoiceDeliveryMethod


class UserBillingPreferences(db.Model):
    """
    User billing and invoice preferences.
    
    Stores user-specific settings for billing, invoicing, and payment reminders.
    Future-proofed for payment provider integration (auto-reload fields nullable).
    One-to-one relationship with User model.
    
    Attributes:
        user_id: Foreign key to User.id
        invoice_email: Custom email for invoices (separate from user email)
        invoice_delivery: Invoice delivery method (email, download_only)
        payment_reminders: Enable payment reminder notifications
        reminder_days_before: Days before due date to send reminders
        auto_reload_enabled: Enable automatic balance reload (future feature)
        auto_reload_threshold: Balance threshold for auto-reload (future feature)
        created_at: Timestamp of preference creation
        updated_at: Timestamp of last update
    
    Relationships:
        user: The User who owns these preferences
    """
    
    __tablename__ = 'user_billing_preferences'
    
    # Primary Key
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign Key (CASCADE delete, one-to-one)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='CASCADE'),
        unique=True,
        nullable=False,
        index=True
    )
    
    # Invoice settings (current features)
    invoice_email = db.Column(db.String(120), nullable=True)  # Custom invoice email
    invoice_delivery = db.Column(
        db.Enum(InvoiceDeliveryMethod),
        default=InvoiceDeliveryMethod.EMAIL,
        nullable=False
    )
    
    # Payment reminders
    payment_reminders = db.Column(db.Boolean, default=True, nullable=False)
    reminder_days_before = db.Column(db.Integer, default=3, nullable=False)  # Days before due date
    
    # Future features (payment provider integration)
    auto_reload_enabled = db.Column(db.Boolean, default=False, nullable=True)
    auto_reload_threshold = db.Column(db.Numeric(10, 2), nullable=True)
    
    # Timestamps
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=True
    )
    
    # Relationships
    user = db.relationship('User', backref=db.backref('billing_preferences', uselist=False, lazy=True))
    
    def to_dict(self):
        """
        Serialize to dictionary for API responses.
        
        Returns:
            dict: Dictionary representation of billing preferences
        """
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
