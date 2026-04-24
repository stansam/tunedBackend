from tuned.extensions import db
from tuned.models.base import BaseModel


class UserNotificationPreferences(BaseModel):
    __tablename__ = 'user_notification_preferences'
    
    user_id = db.Column(
        db.String(36),
        db.ForeignKey('users.id', ondelete='CASCADE'),
        unique=True,
        nullable=False,
        index=True
    )
    
    email_notifications = db.Column(db.Boolean, default=True, nullable=False)
    sms_notifications = db.Column(db.Boolean, default=False, nullable=False)
    push_notifications = db.Column(db.Boolean, default=True, nullable=False)
    
    order_updates = db.Column(db.Boolean, default=True, nullable=False)
    payment_notifications = db.Column(db.Boolean, default=True, nullable=False)
    delivery_notifications = db.Column(db.Boolean, default=True, nullable=False)
    revision_updates = db.Column(db.Boolean, default=True, nullable=False)
    extension_updates = db.Column(db.Boolean, default=True, nullable=False)
    comment_notifications = db.Column(db.Boolean, default=True, nullable=False)
    support_ticket_updates = db.Column(db.Boolean, default=True, nullable=False)
    
    marketing_emails = db.Column(db.Boolean, default=False, nullable=False)
    weekly_summary = db.Column(db.Boolean, default=False, nullable=False)
        
    user = db.relationship('User', foreign_keys=[user_id], backref=db.backref('notification_preferences', uselist=False, lazy=True))
    
    def to_dict(self):
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
