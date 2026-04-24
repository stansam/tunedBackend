from tuned.extensions import db
from tuned.models.enums import ProfileVisibility
from tuned.models.base import BaseModel

class UserPrivacySettings(BaseModel):
    __tablename__ = 'user_privacy_settings'

    user_id = db.Column(
        db.String(36),
        db.ForeignKey('users.id', ondelete='CASCADE'),
        unique=True,
        nullable=False,
        index=True
    )
    
    profile_visibility = db.Column(
        db.Enum(ProfileVisibility),
        default=ProfileVisibility.PRIVATE,
        nullable=False
    )
    show_email = db.Column(db.Boolean, default=False, nullable=False)
    show_phone = db.Column(db.Boolean, default=False, nullable=False)
    show_name = db.Column(db.Boolean, default=True, nullable=False)
    
    allow_messages = db.Column(db.Boolean, default=True, nullable=False)
    allow_comments = db.Column(db.Boolean, default=True, nullable=False)
    
    data_sharing = db.Column(db.Boolean, default=False, nullable=False)
    analytics_tracking = db.Column(db.Boolean, default=True, nullable=False)
    third_party_cookies = db.Column(db.Boolean, default=False, nullable=False)
    
    allow_search_engine_indexing = db.Column(db.Boolean, default=False, nullable=False)
    
    user = db.relationship('User', foreign_keys=[user_id], backref=db.backref('privacy_settings', uselist=False, lazy=True))
    
    def to_dict(self):
        return {
            'profile_visibility': self.profile_visibility.value if self.profile_visibility else 'private',
            'show_email': self.show_email,
            'show_phone': self.show_phone,
            'show_name': self.show_name,
            'allow_messages': self.allow_messages,
            'allow_comments': self.allow_comments,
            'data_sharing': self.data_sharing,
            'analytics_tracking': self.analytics_tracking,
            'third_party_cookies': self.third_party_cookies,
            'allow_search_engine_indexing': self.allow_search_engine_indexing,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<UserPrivacySettings user_id={self.user_id}>'
