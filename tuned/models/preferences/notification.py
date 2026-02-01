"""
User notification preferences model.

This module defines the UserNotificationPreferences model for storing
user-specific notification channel and category preferences.
"""

from datetime import datetime, timezone
from tuned.extensions import db


class UserNotificationPreferences(db.Model):
    """
    User preferences for notifications.
    
    Stores user-specific settings for notification channels (email, SMS, push)
    and granular category controls (order updates, payments, revisions, etc.).
    One-to-one relationship with User model.
    
    Attributes:
        user_id: Foreign key to User.id
        email_notifications: Enable email notifications
        sms_notifications: Enable SMS notifications
        push_notifications: Enable push notifications
        order_updates: Notifications for order status changes
        payment_notifications: Notifications for payment events
        delivery_notifications: Notifications for order delivery
        revision_updates: Notifications for revision requests
        extension_updates: Notifications for deadline extensions
        comment_notifications: Notifications for new comments
        support_ticket_updates: Notifications for support tickets
        marketing_emails: Marketing and promotional emails
        weekly_summary: Weekly digest emails
        created_at: Timestamp of preference creation
        updated_at: Timestamp of last update
    
    Relationships:
        user: The User who owns these preferences
    """
    
    __tablename__ = 'user_notification_preferences'
    
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
    
    # Channel toggles
    email_notifications = db.Column(db.Boolean, default=True, nullable=False)
    sms_notifications = db.Column(db.Boolean, default=False, nullable=False)
    push_notifications = db.Column(db.Boolean, default=True, nullable=False)
    
    # Category toggles (granular control)
    order_updates = db.Column(db.Boolean, default=True, nullable=False)
    payment_notifications = db.Column(db.Boolean, default=True, nullable=False)
    delivery_notifications = db.Column(db.Boolean, default=True, nullable=False)
    revision_updates = db.Column(db.Boolean, default=True, nullable=False)
    extension_updates = db.Column(db.Boolean, default=True, nullable=False)
    comment_notifications = db.Column(db.Boolean, default=True, nullable=False)
    support_ticket_updates = db.Column(db.Boolean, default=True, nullable=False)
    
    # Marketing (can be disabled)
    marketing_emails = db.Column(db.Boolean, default=False, nullable=False)
    weekly_summary = db.Column(db.Boolean, default=False, nullable=False)
    
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
    user = db.relationship('User', backref=db.backref('notification_preferences', uselist=False, lazy=True))
    
    def to_dict(self):
        """
        Serialize to dictionary for API responses.
        
        Returns:
            dict: Dictionary representation of notification preferences
        """
        return {
            'email_notifications': self.email_notifications,
            'sms_notifications': self.sms_notifications,
            'push_notifications': self.push_notifications,
            'order_updates': self.order_updates,
            'payment_notifications': self.payment_notifications,
            'delivery_notifications': self.delivery_notifications,
            'revision_updates': self.revision_updates,
            'extension_updates': self.extension_updates,
            'comment_notifications': self.comment_notifications,
            'support_ticket_updates': self.support_ticket_updates,
            'marketing_emails': self.marketing_emails,
            'weekly_summary': self.weekly_summary,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<UserNotificationPreferences user_id={self.user_id}>'
