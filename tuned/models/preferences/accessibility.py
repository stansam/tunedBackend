"""
User accessibility preferences model.

This module defines the UserAccessibilityPreferences model for storing
user accessibility and usability settings.
"""

from datetime import datetime, timezone
from tuned.extensions import db


class UserAccessibilityPreferences(db.Model):
    """
    User accessibility and usability preferences.
    
    Stores user-specific settings for accessibility features to improve
    usability for users with disabilities or specific needs.
    One-to-one relationship with User model.
    
    Attributes:
        user_id: Foreign key to User.id
        font_size_multiplier: Font size multiplier (0.8 to 2.0, default 1.0)
        high_contrast_mode: Enable high contrast mode
        reduced_motion: Reduce animations and transitions
        screen_reader_optimized: Optimize for screen readers
        keyboard_navigation_enhanced: Enhanced keyboard navigation
        color_blind_mode: Color blind assistance mode
        focus_indicators_enhanced: Enhanced focus indicators
        text_spacing_increased: Increase text spacing
        created_at: Timestamp of preference creation
        updated_at: Timestamp of last update
    
    Relationships:
        user: The User who owns these preferences
    """
    
    __tablename__ = 'user_accessibility_preferences'
    
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
    
    # Font and text settings
    font_size_multiplier = db.Column(
        db.Numeric(3, 2),
        default=1.0,
        nullable=False
    )  # 0.8 to 2.0
    text_spacing_increased = db.Column(db.Boolean, default=False, nullable=False)
    
    # Visual modes
    high_contrast_mode = db.Column(db.Boolean, default=False, nullable=False)
    color_blind_mode = db.Column(db.Boolean, default=False, nullable=False)
    
    # Motion and animation
    reduced_motion = db.Column(db.Boolean, default=False, nullable=False)
    
    # Navigation and interaction
    screen_reader_optimized = db.Column(db.Boolean, default=False, nullable=False)
    keyboard_navigation_enhanced = db.Column(db.Boolean, default=False, nullable=False)
    focus_indicators_enhanced = db.Column(db.Boolean, default=False, nullable=False)
    
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
    user = db.relationship('User', backref=db.backref('accessibility_preferences', uselist=False, lazy=True))
    
    def to_dict(self):
        """
        Serialize to dictionary for API responses.
        
        Returns:
            dict: Dictionary representation of accessibility preferences
        """
        return {
            'font_size_multiplier': float(self.font_size_multiplier) if self.font_size_multiplier else 1.0,
            'text_spacing_increased': self.text_spacing_increased,
            'high_contrast_mode': self.high_contrast_mode,
            'color_blind_mode': self.color_blind_mode,
            'reduced_motion': self.reduced_motion,
            'screen_reader_optimized': self.screen_reader_optimized,
            'keyboard_navigation_enhanced': self.keyboard_navigation_enhanced,
            'focus_indicators_enhanced': self.focus_indicators_enhanced,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<UserAccessibilityPreferences user_id={self.user_id}>'
