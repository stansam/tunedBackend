from tuned.extensions import db
from tuned.models.enums import InvoiceDeliveryMethod
from tuned.models.base import BaseModel
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING, Optional, Any
from decimal import Decimal

if TYPE_CHECKING:
    from tuned.models.user import User

class UserBillingPreferences(BaseModel):
    __tablename__ = 'user_billing_preferences'
    
    user_id: Mapped[str] = mapped_column(
        db.String(36),
        db.ForeignKey('users.id', ondelete='CASCADE'),
        unique=True,
        nullable=False,
        index=True
    )
    
    invoice_email: Mapped[Optional[str]] = mapped_column(db.String(120), nullable=True)
    invoice_delivery: Mapped[InvoiceDeliveryMethod] = mapped_column(
        db.Enum(InvoiceDeliveryMethod),
        default=InvoiceDeliveryMethod.EMAIL,
        nullable=False
    )
    
    payment_reminders: Mapped[bool] = mapped_column(db.Boolean, default=True, nullable=False)
    reminder_days_before: Mapped[int] = mapped_column(db.Integer, default=3, nullable=False)
    
    auto_reload_enabled: Mapped[Optional[bool]] = mapped_column(db.Boolean, default=False, nullable=True)
    auto_reload_threshold: Mapped[Optional[Decimal]] = mapped_column(db.Numeric(10, 2), nullable=True)
    
    user: Mapped["User"] = relationship('User', foreign_keys=[user_id], back_populates='billing_preferences')
    
    def to_dict(self) -> dict[str, Any]:
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
    
    def __repr__(self) -> str:
        return f'<UserBillingPreferences user_id={self.user_id}>'
