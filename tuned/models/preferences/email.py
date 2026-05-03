from tuned.extensions import db
from tuned.models.enums import EmailFrequency
from tuned.models.base import BaseModel
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING, Optional, Any

if TYPE_CHECKING:
    from tuned.models.user import User

class UserEmailPreferences(BaseModel):
    __tablename__ = 'user_email_preferences'
    
    user_id: Mapped[str] = mapped_column(
        db.String(36),
        db.ForeignKey('users.id', ondelete='CASCADE'),
        unique=True,
        nullable=False,
        index=True
    )
    
    newsletter: Mapped[bool] = mapped_column(db.Boolean, default=False, nullable=False)
    promotional_emails: Mapped[bool] = mapped_column(db.Boolean, default=False, nullable=False)
    product_updates: Mapped[bool] = mapped_column(db.Boolean, default=True, nullable=False)
    
    order_confirmations: Mapped[bool] = mapped_column(
        db.Boolean,
        default=True,
        server_default='true',
        nullable=False
    )
    payment_receipts: Mapped[bool] = mapped_column(
        db.Boolean,
        default=True,
        server_default='true',
        nullable=False
    )
    account_security: Mapped[bool] = mapped_column(
        db.Boolean,
        default=True,
        server_default='true',
        nullable=False
    )
    
    frequency: Mapped[EmailFrequency] = mapped_column(
        db.Enum(EmailFrequency),
        default=EmailFrequency.INSTANT,
        nullable=False
    )
    
    daily_digest_hour: Mapped[Optional[int]] = mapped_column(
        db.Integer,
        default=9,
        nullable=True
    )  # 0-23, null if instant
    
    user: Mapped["User"] = relationship('User', foreign_keys=[user_id], back_populates='email_preferences')
    
    def to_dict(self) -> dict[str, Any]:
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
    
    def __repr__(self) -> str:
        return f'<UserEmailPreferences user_id={self.user_id}>'
