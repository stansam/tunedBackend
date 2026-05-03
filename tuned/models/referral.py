from tuned.extensions import db
from tuned.models.base import BaseModel
from datetime import datetime, timezone
from tuned.models.enums import ReferralStatus
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from tuned.models.user import User

class Referral(BaseModel):
    __tablename__ = 'referrals'
    referrer_id: Mapped[Optional[str]] = mapped_column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    referred_id: Mapped[Optional[str]] = mapped_column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    code: Mapped[str] = mapped_column(db.String(10), unique=True, nullable=False)
    status: Mapped[ReferralStatus] = mapped_column(db.Enum(ReferralStatus), default=ReferralStatus.PENDING, nullable=False)
    points_earned: Mapped[int] = mapped_column(db.Integer, default=0, nullable=False)
    points_used: Mapped[int] = mapped_column(db.Integer, default=0, nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime(timezone=True), nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime(timezone=True), nullable=True)
    
    __table_args__ = (
        db.Index('ix_referral_referrer_status', 'referrer_id', 'status'),
        db.CheckConstraint('points_earned >= 0', name='valid_points'),
        db.CheckConstraint('referrer_id != referred_id', name='no_self_referral'),
    )

    referrer: Mapped[Optional["User"]] = relationship('User', foreign_keys=[referrer_id], back_populates='referrals')
    referred: Mapped[Optional["User"]] = relationship('User', foreign_keys=[referred_id], back_populates='referred_by')
    
    def __repr__(self) -> str:
        return f'<Referral {self.code}>'