"""
Validation schema for user email preferences.

Handles validation for email communication preferences with
critical email protection (order confirmations, payment receipts, security).
"""

from marshmallow import Schema, fields, validates, ValidationError, validate, post_load


class EmailPreferencesSchema(Schema):
    """Validation schema for email communication preferences."""
    
    # Optional emails (can be disabled)
    newsletter = fields.Boolean(required=False, allow_none=True)
    promotional_emails = fields.Boolean(required=False, allow_none=True)
    product_updates = fields.Boolean(required=False, allow_none=True)
    
    # Critical emails (CANNOT be disabled)
    order_confirmations = fields.Boolean(required=False, allow_none=True)
    payment_receipts = fields.Boolean(required=False, allow_none=True)
    account_security = fields.Boolean(required=False, allow_none=True)
    
    # Frequency settings
    frequency = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.OneOf(['instant', 'daily', 'weekly'])
    )
    
    daily_digest_hour = fields.Integer(
        required=False,
        allow_none=True,
        validate=validate.Range(min=0, max=23)
    )
    
    @post_load
    def set_defaults(self, data, **kwargs):
        """Set default values for email preferences."""
        data.setdefault('newsletter', False)
        data.setdefault('promotional_emails', False)
        data.setdefault('product_updates', True)
        # Critical emails always True
        data.setdefault('order_confirmations', True)
        data.setdefault('payment_receipts', True)
        data.setdefault('account_security', True)
        data.setdefault('frequency', 'instant')
        data.setdefault('daily_digest_hour', 9)
        return data
    
    @validates('order_confirmations')
    def validate_order_confirmations(self, value):
        """Ensure order confirmations cannot be disabled."""
        if value is False:
            raise ValidationError('Order confirmation emails cannot be disabled for security reasons')
    
    @validates('payment_receipts')
    def validate_payment_receipts(self, value):
        """Ensure payment receipts cannot be disabled."""
        if value is False:
            raise ValidationError('Payment receipt emails cannot be disabled for security reasons')
    
    @validates('account_security')
    def validate_account_security(self, value):
        """Ensure security emails cannot be disabled."""
        if value is False:
            raise ValidationError('Security emails cannot be disabled')
