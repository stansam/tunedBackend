from tuned.extensions import db
from tuned.models.base import BaseModel
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING, Any
from decimal import Decimal

if TYPE_CHECKING:
    from tuned.models.user import User

class UserAccessibilityPreferences(BaseModel):
    __tablename__ = 'user_accessibility_preferences'
        
    user_id: Mapped[str] = mapped_column(
        db.String(36),
        db.ForeignKey('users.id', ondelete='CASCADE'),
        unique=True,
        nullable=False,
        index=True
    )
    
    font_size_multiplier: Mapped[Decimal] = mapped_column(
        db.Numeric(3, 2),
        default=Decimal('1.00'),
        nullable=False
    )  # 0.8 to 2.0
    text_spacing_increased: Mapped[bool] = mapped_column(db.Boolean, default=False, nullable=False)
    
    high_contrast_mode: Mapped[bool] = mapped_column(db.Boolean, default=False, nullable=False)
    color_blind_mode: Mapped[bool] = mapped_column(db.Boolean, default=False, nullable=False)
    
    reduced_motion: Mapped[bool] = mapped_column(db.Boolean, default=False, nullable=False)
    
    screen_reader_optimized: Mapped[bool] = mapped_column(db.Boolean, default=False, nullable=False)
    keyboard_navigation_enhanced: Mapped[bool] = mapped_column(db.Boolean, default=False, nullable=False)
    focus_indicators_enhanced: Mapped[bool] = mapped_column(db.Boolean, default=False, nullable=False)
    
    user: Mapped["User"] = relationship('User', foreign_keys=[user_id], back_populates='accessibility_preferences')
    
    def to_dict(self) -> dict[str, Any]:
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
    
    def __repr__(self) -> str:
        return f'<UserAccessibilityPreferences user_id={self.user_id}>'
