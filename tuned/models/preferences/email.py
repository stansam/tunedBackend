from tuned.extensions import db
from tuned.models.enums import EmailFrequency
from tuned.models.base import BaseModel


class UserEmailPreferences(BaseModel):
    __tablename__ = 'user_email_preferences'
    
    user_id = db.Column(
        db.String(36),
        db.ForeignKey('users.id', ondelete='CASCADE'),
        unique=True,
        nullable=False,
        index=True
    )
    
    newsletter = db.Column(db.Boolean, default=False, nullable=False)
    promotional_emails = db.Column(db.Boolean, default=False, nullable=False)
    product_updates = db.Column(db.Boolean, default=True, nullable=False)
    
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
    
    frequency = db.Column(
        db.Enum(EmailFrequency),
        default=EmailFrequency.INSTANT,
        nullable=False
    )
    
    daily_digest_hour = db.Column(
        db.Integer,
        default=9,
        nullable=True
    )  # 0-23, null if instant
    
    user = db.relationship('User', foreign_keys=[user_id], backref=db.backref('email_preferences', uselist=False, lazy=True))
    
    def to_dict(self):
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
