from tuned.extensions import db
from tuned.models.base import BaseModel


class UserAccessibilityPreferences(BaseModel):
    __tablename__ = 'user_accessibility_preferences'
        
    user_id = db.Column(
        db.String(36),
        db.ForeignKey('users.id', ondelete='CASCADE'),
        unique=True,
        nullable=False,
        index=True
    )
    
    font_size_multiplier = db.Column(
        db.Numeric(3, 2),
        default=1.0,
        nullable=False
    )  # 0.8 to 2.0
    text_spacing_increased = db.Column(db.Boolean, default=False, nullable=False)
    
    high_contrast_mode = db.Column(db.Boolean, default=False, nullable=False)
    color_blind_mode = db.Column(db.Boolean, default=False, nullable=False)
    
    reduced_motion = db.Column(db.Boolean, default=False, nullable=False)
    
    screen_reader_optimized = db.Column(db.Boolean, default=False, nullable=False)
    keyboard_navigation_enhanced = db.Column(db.Boolean, default=False, nullable=False)
    focus_indicators_enhanced = db.Column(db.Boolean, default=False, nullable=False)
    
    
    user = db.relationship('User', foreign_keys=[user_id], backref=db.backref('accessibility_preferences', uselist=False, lazy=True))
    
    def to_dict(self):
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
