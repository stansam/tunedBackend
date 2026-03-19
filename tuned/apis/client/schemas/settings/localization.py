"""
Validation schema for user localization settings.

Handles validation for language, timezone, date/time/number formats,
currency, and calendar preferences.
"""

from marshmallow import Schema, fields, validate, post_load


class LocalizationSettingsSchema(Schema):
    """Validation schema for localization settings."""
    
    # Language & Locale
    language = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.OneOf(['en', 'es', 'fr', 'de', 'pt', 'zh', 'ar', 'ja', 'it', 'ru'])
    )
    
    country_code = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.Length(equal=2)  # ISO 3166-1 alpha-2
    )
    
    # Timezone
    timezone = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.Length(max=50)
    )
    
    # Date & Time Formats
    date_format = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.OneOf(['MM/DD/YYYY', 'DD/MM/YYYY', 'YYYY-MM-DD'])
    )
    
    time_format = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.OneOf(['12h', '24h'])
    )
    
    # Number & Currency
    currency = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.OneOf(['USD', 'EUR', 'GBP', 'CAD', 'AUD', 'JPY', 'CNY'])
    )
    
    number_format = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.OneOf(['1,234.56', '1.234,56', '1 234,56'])
    )
    
    # Calendar
    week_start = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.OneOf(['sunday', 'monday'])
    )
    
    @post_load
    def set_defaults(self, data, **kwargs):
        """Set default values for localization settings."""
        data.setdefault('language', 'en')
        data.setdefault('timezone', 'UTC')
        data.setdefault('date_format', 'MM/DD/YYYY')
        data.setdefault('time_format', '12h')
        data.setdefault('currency', 'USD')
        data.setdefault('number_format', '1,234.56')
        data.setdefault('week_start', 'sunday')
        return data


# Keep LanguagePreferenceSchema for backward compatibility
LanguagePreferenceSchema = LocalizationSettingsSchema
