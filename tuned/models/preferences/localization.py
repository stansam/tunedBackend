"""
User localization settings model.

This module defines the UserLocalizationSettings model for storing
user language, timezone, and formatting preferences.
"""

from datetime import datetime, timezone
from tuned.extensions import db
from tuned.models.enums import DateFormat, TimeFormat, NumberFormat, WeekStart


class UserLocalizationSettings(db.Model):
    """
    User language, timezone, and formatting preferences.
    
    Stores user-specific settings for language, locale, timezone,
    and various formatting options (date, time, numbers, currency).
    One-to-one relationship with User model.
    
    Note: User.language and User.timezone fields act as cached values
    for performance. This model is the authoritative source.
    
    Attributes:
        user_id: Foreign key to User.id
        language: Language code (ISO 639-1, e.g., 'en', 'es')
        country_code: Country code (ISO 3166-1 alpha-2, e.g., 'US', 'GB')
        timezone: Timezone (IANA timezone, e.g., 'America/New_York')
        date_format: Date format preference (MM/DD/YYYY, DD/MM/YYYY, YYYY-MM-DD)
        time_format: Time format preference (12h, 24h)
        currency: Currency code (ISO 4217, e.g., 'USD', 'EUR')
        number_format: Number format preference (1,234.56, 1.234,56, 1 234,56)
        week_start: First day of week (sunday, monday)
        created_at: Timestamp of preference creation
        updated_at: Timestamp of last update
    
    Relationships:
        user: The User who owns these preferences
    """
    
    __tablename__ = 'user_localization_settings'
    
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
    
    # Language & Locale
    language = db.Column(db.String(10), default='en', nullable=False)  # ISO 639-1
    country_code = db.Column(db.String(2), default='US', nullable=True)  # ISO 3166-1 alpha-2
    
    # Timezone
    timezone = db.Column(db.String(50), default='UTC', nullable=False)  # IANA timezone
    
    # Date & Time formatting
    date_format = db.Column(
        db.Enum(DateFormat),
        default=DateFormat.MM_DD_YYYY,
        nullable=False
    )
    time_format = db.Column(
        db.Enum(TimeFormat),
        default=TimeFormat.TWELVE_HOUR,
        nullable=False
    )
    
    # Number & Currency formatting
    currency = db.Column(db.String(3), default='USD', nullable=False)  # ISO 4217
    number_format = db.Column(
        db.Enum(NumberFormat),
        default=NumberFormat.COMMA_DOT,
        nullable=False
    )
    
    # Calendar preferences
    week_start = db.Column(
        db.Enum(WeekStart),
        default=WeekStart.SUNDAY,
        nullable=False
    )
    
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
    user = db.relationship('User', backref=db.backref('localization_settings', uselist=False, lazy=True))
    
    def to_dict(self):
        """
        Serialize to dictionary for API responses.
        
        Returns:
            dict: Dictionary representation of localization settings
        """
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
    
    def __repr__(self):
        return f'<UserLocalizationSettings user_id={self.user_id} language={self.language} timezone={self.timezone}>'
