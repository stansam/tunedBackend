"""
Validation schema for user billing preferences.

Handles validation for invoice delivery preferences,
payment reminders, and future auto-reload settings.
"""

from marshmallow import Schema, fields, validate, post_load


class BillingPreferencesSchema(Schema):
    """Validation schema for billing preferences."""
    
    invoice_email = fields.Email(
        required=False,
        allow_none=True,
        validate=validate.Length(max=120)
    )
    
    invoice_delivery = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.OneOf(['email', 'download_only'])
    )
    
    payment_reminders = fields.Boolean(required=False, allow_none=True)
    
    reminder_days_before = fields.Integer(
        required=False,
        allow_none=True,
        validate=validate.Range(min=1, max=30)
    )
    
    # Future features (payment provider integration)
    auto_reload_enabled = fields.Boolean(required=False, allow_none=True)
    
    auto_reload_threshold = fields.Float(
        required=False,
        allow_none=True,
        validate=validate.Range(min=0, max=10000)
    )
    
    @post_load
    def set_defaults(self, data, **kwargs):
        """Set default values for billing preferences."""
        data.setdefault('invoice_delivery', 'email')
        data.setdefault('payment_reminders', True)
        data.setdefault('reminder_days_before', 3)
        return data
