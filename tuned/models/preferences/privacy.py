"""
User privacy settings model.

This module defines the UserPrivacySettings model for storing
user privacy and visibility preferences.
"""

from datetime import datetime, timezone
from tuned.extensions import db
from tuned.models.enums import ProfileVisibility


class UserPrivacySettings(db.Model):
    """
    User privacy and visibility preferences.
    
    Stores user-specific settings for profile visibility, data sharing,
    and communication controls. One-to-one relationship with User model.
    
    Attributes:
        user_id: Foreign key to User.id
        profile_visibility: Profile visibility level (public, private, friends_only)
        show_email: Display email address on profile
        show_phone: Display phone number on profile
        show_name: Display full name on profile
        allow_messages: Allow messages from other users
        allow_comments: Allow comments on user content
        data_sharing: Allow data sharing with third parties
        analytics_tracking: Allow analytics tracking
        third_party_cookies: Allow third-party cookies
        allow_search_engine_indexing: Allow search engines to index profile
        created_at: Timestamp of preference creation
        updated_at: Timestamp of last update
    
    Relationships:
        user: The User who owns these preferences
    """
    
    __tablename__ = 'user_privacy_settings'
    
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
    
    # Profile visibility
    profile_visibility = db.Column(
        db.Enum(ProfileVisibility),
        default=ProfileVisibility.PRIVATE,
        nullable=False
    )
    show_email = db.Column(db.Boolean, default=False, nullable=False)
    show_phone = db.Column(db.Boolean, default=False, nullable=False)
    show_name = db.Column(db.Boolean, default=True, nullable=False)
    
    # Communication settings
    allow_messages = db.Column(db.Boolean, default=True, nullable=False)
    allow_comments = db.Column(db.Boolean, default=True, nullable=False)
    
    # Data sharing & tracking
    data_sharing = db.Column(db.Boolean, default=False, nullable=False)
    analytics_tracking = db.Column(db.Boolean, default=True, nullable=False)
    third_party_cookies = db.Column(db.Boolean, default=False, nullable=False)
    
    # Search engine indexing
    allow_search_engine_indexing = db.Column(db.Boolean, default=False, nullable=False)
    
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
    user = db.relationship('User', backref=db.backref('privacy_settings', uselist=False, lazy=True))
    
    def to_dict(self):
        """
        Serialize to dictionary for API responses.
        
        Returns:
            dict: Dictionary representation of privacy settings
        """
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
