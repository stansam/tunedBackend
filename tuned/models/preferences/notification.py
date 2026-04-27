from tuned.extensions import db
from tuned.models.base import BaseModel
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from tuned.models.user import User

class UserNotificationPreferences(BaseModel):
    __tablename__ = 'user_notification_preferences'
    
    user_id: Mapped[str] = mapped_column(
        db.String(36),
        db.ForeignKey('users.id', ondelete='CASCADE'),
        unique=True,
        nullable=False,
        index=True
    )
    
    email_notifications: Mapped[bool] = mapped_column(db.Boolean, default=True, nullable=False)
    sms_notifications: Mapped[bool] = mapped_column(db.Boolean, default=False, nullable=False)
    push_notifications: Mapped[bool] = mapped_column(db.Boolean, default=True, nullable=False)
    
    order_updates: Mapped[bool] = mapped_column(db.Boolean, default=True, nullable=False)
    payment_notifications: Mapped[bool] = mapped_column(db.Boolean, default=True, nullable=False)
    delivery_notifications: Mapped[bool] = mapped_column(db.Boolean, default=True, nullable=False)
    revision_updates: Mapped[bool] = mapped_column(db.Boolean, default=True, nullable=False)
    extension_updates: Mapped[bool] = mapped_column(db.Boolean, default=True, nullable=False)
    comment_notifications: Mapped[bool] = mapped_column(db.Boolean, default=True, nullable=False)
    support_ticket_updates: Mapped[bool] = mapped_column(db.Boolean, default=True, nullable=False)
    
    marketing_emails: Mapped[bool] = mapped_column(db.Boolean, default=False, nullable=False)
    weekly_summary: Mapped[bool] = mapped_column(db.Boolean, default=False, nullable=False)
        
    user: Mapped["User"] = relationship('User', foreign_keys=[user_id], back_populates='notification_preferences')
    
    def to_dict(self) -> dict[str, Any]:
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
    
    def __repr__(self) -> str:
        return f'<UserNotificationPreferences user_id={self.user_id}>'
