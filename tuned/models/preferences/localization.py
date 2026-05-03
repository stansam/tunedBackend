from tuned.extensions import db
from tuned.models.enums import DateFormat, TimeFormat, NumberFormat, WeekStart
from tuned.models.base import BaseModel
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING, Optional, Any

if TYPE_CHECKING:
    from tuned.models.user import User

class UserLocalizationSettings(BaseModel):
    __tablename__ = 'user_localization_settings'
    
    user_id: Mapped[str] = mapped_column(
        db.String(36),
        db.ForeignKey('users.id', ondelete='CASCADE'),
        unique=True,
        nullable=False,
        index=True
    )
    
    language: Mapped[str] = mapped_column(db.String(10), default='en', nullable=False)  # ISO 639-1
    country_code: Mapped[Optional[str]] = mapped_column(db.String(2), default='US', nullable=True)  # ISO 3166-1 alpha-2
    
    timezone: Mapped[str] = mapped_column(db.String(50), default='UTC', nullable=False)  # IANA timezone
    
    date_format: Mapped[DateFormat] = mapped_column(
        db.Enum(DateFormat),
        default=DateFormat.MM_DD_YYYY,
        nullable=False
    )
    time_format: Mapped[TimeFormat] = mapped_column(
        db.Enum(TimeFormat),
        default=TimeFormat.TWELVE_HOUR,
        nullable=False
    )
    
    currency: Mapped[str] = mapped_column(db.String(3), default='USD', nullable=False)  # ISO 4217
    number_format: Mapped[NumberFormat] = mapped_column(
        db.Enum(NumberFormat),
        default=NumberFormat.COMMA_DOT,
        nullable=False
    )
    
    week_start: Mapped[WeekStart] = mapped_column(
        db.Enum(WeekStart),
        default=WeekStart.SUNDAY,
        nullable=False
    )
        
    user: Mapped["User"] = relationship('User', foreign_keys=[user_id], back_populates='localization_settings')
    
    def to_dict(self) -> dict[str, Any]:
        return {
            'language': self.language,
            'country_code': self.country_code,
            'timezone': self.timezone,
            'date_format': self.date_format.value if self.date_format else 'MM/DD/YYYY',
            'time_format': self.time_format.value if self.time_format else '12h',
            'currency': self.currency,
            'number_format': self.number_format.value if self.number_format else '1,234.56',
            'week_start': self.week_start.value if self.week_start else 'sunday',
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self) -> str:
        return f'<UserLocalizationSettings user_id={self.user_id} language={self.language} timezone={self.timezone}>'
