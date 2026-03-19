"""
Validation schemas for user profile updates.

This module contains Marshmallow schemas for validating profile
update requests including personal information and preferences.
"""

from marshmallow import Schema, fields, validates, ValidationError, validate, post_load
from tuned.models.user import GenderEnum


class UpdateProfileSchema(Schema):
    """Validation schema for updating user profile information."""
    
    first_name = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.Length(min=1, max=50),
        error_messages={
            'min_length': 'First name must be at least 1 character',
            'max_length': 'First name cannot exceed 50 characters'
        }
    )
    
    last_name = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.Length(min=1, max=50),
        error_messages={
            'min_length': 'Last name must be at least 1 character',
            'max_length': 'Last name cannot exceed 50 characters'
        }
    )
    
    phone = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.Regexp(
            r'^\+?[1-9]\d{1,14}$',
            error='Invalid phone number format. Use international format (e.g., +1234567890)'
        )
    )
    
    gender = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.OneOf([g.value for g in GenderEnum])
    )
    
    date_of_birth = fields.Date(
        required=False,
        allow_none=True,
        format='%Y-%m-%d'
    )
    
    bio = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.Length(max=500),
        error_messages={'max_length': 'Bio cannot exceed 500 characters'}
    )
    
    country = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.Length(max=100)
    )
    
    city = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.Length(max=100)
    )
    
    timezone = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.Length(max=50)
    )
    
    @post_load
    def strip_strings(self, data, **kwargs):
        """Strip whitespace from string fields."""
        string_fields = ['first_name', 'last_name', 'bio', 'country', 'city', 'timezone']
        for field in string_fields:
            if field in data and data[field]:
                data[field] = data[field].strip()
        return data
    
    @validates('date_of_birth')
    def validate_age(self, value):
        """Ensure user is at least 13 years old."""
        from datetime import date
        
        if value:
            today = date.today()
            age = today.year - value.year - ((today.month, today.day) < (value.month, value.day))
            
            if age < 13:
                raise ValidationError('You must be at least 13 years old')
            
            if age > 120:
                raise ValidationError('Invalid date of birth')


class UpdateProfilePictureSchema(Schema):
    """Validation schema for profile picture upload."""
    
    image_format = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.OneOf(['jpeg', 'jpg', 'png', 'gif', 'webp'])
    )
    
    crop_data = fields.Dict(
        required=False,
        allow_none=True
    )


class DeleteProfilePictureSchema(Schema):
    """Validation schema for deleting profile picture."""
    
    confirm = fields.Boolean(
        required=True,
        validate=validate.Equal(True, error='Confirmation required')
    )


class NotificationPreferencesSchema(Schema):
    """Validation schema for notification preferences."""
    
    email_notifications = fields.Boolean(required=False, allow_none=True)
    sms_notifications = fields.Boolean(required=False, allow_none=True)
    push_notifications = fields.Boolean(required=False, allow_none=True)
    order_updates = fields.Boolean(required=False, allow_none=True)
    payment_notifications = fields.Boolean(required=False, allow_none=True)
    delivery_notifications = fields.Boolean(required=False, allow_none=True)
    marketing_emails = fields.Boolean(required=False, allow_none=True)
    weekly_summary = fields.Boolean(required=False, allow_none=True)
    comment_notifications = fields.Boolean(required=False, allow_none=True)
    support_ticket_updates = fields.Boolean(required=False, allow_none=True)
    
    @post_load
    def set_defaults(self, data, **kwargs):
        """Set default values."""
        data.setdefault('email_notifications', True)
        data.setdefault('sms_notifications', False)
        data.setdefault('push_notifications', True)
        data.setdefault('order_updates', True)
        data.setdefault('payment_notifications', True)
        data.setdefault('delivery_notifications', True)
        data.setdefault('marketing_emails', False)
        data.setdefault('weekly_summary', False)
        data.setdefault('comment_notifications', True)
        data.setdefault('support_ticket_updates', True)
        return data


class PrivacySettingsSchema(Schema):
    """Validation schema for privacy settings."""
    
    profile_visibility = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.OneOf(['public', 'private', 'friends_only'])
    )
    
    show_email = fields.Boolean(required=False, allow_none=True)
    show_phone = fields.Boolean(required=False, allow_none=True)
    allow_messages = fields.Boolean(required=False, allow_none=True)
    data_sharing = fields.Boolean(required=False, allow_none=True)
    analytics_tracking = fields.Boolean(required=False, allow_none=True)
    
    @post_load
    def set_defaults(self, data, **kwargs):
        """Set default values."""
        data.setdefault('profile_visibility', 'private')
        data.setdefault('show_email', False)
        data.setdefault('show_phone', False)
        data.setdefault('allow_messages', True)
        data.setdefault('data_sharing', False)
        data.setdefault('analytics_tracking', True)
        return data


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


class EmailPreferencesSchema(Schema):
    """Validation schema for email communication preferences."""
    
    newsletter = fields.Boolean(required=False, allow_none=True)
    promotional_emails = fields.Boolean(required=False, allow_none=True)
    product_updates = fields.Boolean(required=False, allow_none=True)
    
    order_confirmations = fields.Boolean(
        required=False,
        allow_none=True
    )
    
    payment_receipts = fields.Boolean(
        required=False,
        allow_none=True
    )
    
    account_security = fields.Boolean(
        required=False,
        allow_none=True
    )
    
    frequency = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.OneOf(['instant', 'daily', 'weekly'])
    )
    
    @post_load
    def set_defaults(self, data, **kwargs):
        """Set default values."""
        data.setdefault('newsletter', False)
        data.setdefault('promotional_emails', False)
        data.setdefault('product_updates', True)
        # These cannot be disabled for security
        data.setdefault('order_confirmations', True)
        data.setdefault('payment_receipts', True)
        data.setdefault('account_security', True)
        data.setdefault('frequency', 'instant')
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
