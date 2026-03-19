from marshmallow import Schema, fields, validate, post_load

class LanguagePreferenceSchema(Schema):
    """Validation schema for language preferences."""
    
    language = fields.Str(
        required=True,
        validate=validate.OneOf(['en', 'es', 'fr', 'de', 'pt', 'zh', 'ar']),
        error_messages={'required': 'Language is required'}
    )
    
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
    
    currency = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.OneOf(['USD', 'EUR', 'GBP', 'CAD', 'AUD'])
    )
    
    @post_load
    def set_defaults(self, data, **kwargs):
        """Set default values."""
        data.setdefault('date_format', 'MM/DD/YYYY')
        data.setdefault('time_format', '12h')
        data.setdefault('currency', 'USD')
        return data

