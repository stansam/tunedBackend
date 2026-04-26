from tuned.extensions import db
from tuned.models.base import BaseModel
from datetime import datetime, timezone
from tuned.models.enums import ReferralStatus

class Referral(BaseModel):
    __tablename__ = 'referrals'
    referrer_id = db.Column(db.String(36), db.ForeignKey('users.id'))
    referred_id = db.Column(db.String(36), db.ForeignKey('users.id'))
    code = db.Column(db.String(10), unique=True, nullable=False)
    status = db.Column(db.Enum(ReferralStatus), default=ReferralStatus.PENDING, nullable=False)
    points_earned = db.Column(db.Integer, default=0)
    points_used = db.Column(db.Integer, default=0)
    completed_at = db.Column(db.DateTime(timezone=True), nullable=True)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=True)
    
    __table_args__ = (
        db.Index('ix_referral_referrer_status', 'referrer_id', 'status'),
        db.CheckConstraint('points_earned >= 0', name='valid_points'),
        db.CheckConstraint('referrer_id != referred_id', name='no_self_referral'),
    )
    
    def __repr__(self):
        return f'<Referral {self.code}>'