import uuid
from typing import Optional, TYPE_CHECKING, Any
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, ENUM
from datetime import datetime, timezone
from tuned.extensions import db
from tuned.models.base import BaseModel
from tuned.models.enums import ReferralStatus

if TYPE_CHECKING:
    from tuned.models.user import User

class Referral(BaseModel):
    __tablename__ = 'referrals'
    referrer_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=True, index=True)
    referred_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=True, index=True)
    code: Mapped[str] = mapped_column(db.String(10), unique=True, nullable=False)
    status: Mapped[ReferralStatus] = mapped_column(ENUM(ReferralStatus, name="referralstatus"), default=ReferralStatus.PENDING, nullable=False)
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
    
    def __init__(self, **kwargs: Any) -> None:
        super(Referral, self).__init__(**kwargs)
    
    def __repr__(self) -> str:
        return f'<Referral {self.code}>'