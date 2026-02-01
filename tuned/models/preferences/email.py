"""
User email preferences model.

This module defines the UserEmailPreferences model for storing
user-specific email communication preferences.
"""

from datetime import datetime, timezone
from tuned.extensions import db
from tuned.models.enums import EmailFrequency


class UserEmailPreferences(db.Model):
    """
    User preferences for email communications.
    
    Stores user-specific settings for email categories and delivery frequency.
    Critical emails (order confirmations, payment receipts, security alerts) 
    cannot be disabled for security and compliance reasons.
    One-to-one relationship with User model.
    
    Attributes:
        user_id: Foreign key to User.id
        newsletter: Enable newsletter subscription
        promotional_emails: Enable promotional emails
        product_updates: Enable product update emails
        order_confirmations: Order confirmation emails (CANNOT BE DISABLED)
        payment_receipts: Payment receipt emails (CANNOT BE DISABLED)
        account_security: Account security emails (CANNOT BE DISABLED)
        frequency: Email delivery frequency (instant, daily, weekly)
        daily_digest_hour: Hour of day for daily digest (0-23, null if instant)
        created_at: Timestamp of preference creation
        updated_at: Timestamp of last update
    
    Relationships:
        user: The User who owns these preferences
    """
    
    __tablename__ = 'user_email_preferences'
    
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
    
    # Email categories (can be disabled)
    newsletter = db.Column(db.Boolean, default=False, nullable=False)
    promotional_emails = db.Column(db.Boolean, default=False, nullable=False)
    product_updates = db.Column(db.Boolean, default=True, nullable=False)
    
    # Critical emails (CANNOT be disabled - server_default ensures DB-level enforcement)
    order_confirmations = db.Column(
        db.Boolean,
        default=True,
        server_default='true',
        nullable=False
    )
    payment_receipts = db.Column(
        db.Boolean,
        default=True,
        server_default='true',
        nullable=False
    )
    account_security = db.Column(
        db.Boolean,
        default=True,
        server_default='true',
        nullable=False
    )
    
    # Frequency control
    frequency = db.Column(
        db.Enum(EmailFrequency),
        default=EmailFrequency.INSTANT,
        nullable=False
    )
    
    # Digest options
    daily_digest_hour = db.Column(
        db.Integer,
        default=9,
        nullable=True
    )  # 0-23, null if instant
    
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
    user = db.relationship('User', backref=db.backref('email_preferences', uselist=False, lazy=True))
    
    def to_dict(self):
        """
        Serialize to dictionary for API responses.
        
        Returns:
            dict: Dictionary representation of email preferences
        """
        return {
            'newsletter': self.newsletter,
            'promotional_emails': self.promotional_emails,
            'product_updates': self.product_updates,
            'order_confirmations': self.order_confirmations,
            'payment_receipts': self.payment_receipts,
            'account_security': self.account_security,
            'frequency': self.frequency.value if self.frequency else 'instant',
            'daily_digest_hour': self.daily_digest_hour,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<UserEmailPreferences user_id={self.user_id}>'
