"""
Validation schemas for newsletter subscription operations.

This module contains Marshmallow schemas for validating newsletter
subscription and unsubscription requests.
"""

from marshmallow import Schema, fields, validate, post_load


class NewsletterSubscribeSchema(Schema):
    """Validation schema for newsletter subscription."""
    
    email = fields.Email(
        required=False,
        allow_none=True,
        error_messages={'invalid': 'Invalid email address'}
    )
    
    name = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.Length(max=100)
    )
    
    preferences = fields.Dict(
        required=False,
        allow_none=True
    )
    
    topics = fields.List(
        fields.Str(),
        required=False,
        allow_none=True
    )


class NewsletterUnsubscribeSchema(Schema):
    """Validation schema for newsletter unsubscription."""
    
    reason = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.OneOf([
            'too_many_emails',
            'not_relevant',
            'never_signed_up',
            'privacy_concerns',
            'other'
        ])
    )
    
    feedback = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.Length(max=500)
    )
    
    unsubscribe_all = fields.Boolean(
        required=False,
        allow_none=True
    )
    
    @post_load
    def set_defaults(self, data, **kwargs):
        """Set default values."""
        data.setdefault('unsubscribe_all', True)
        return data


class NewsletterPreferencesSchema(Schema):
    """Validation schema for newsletter preferences."""
    
    frequency = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.OneOf(['daily', 'weekly', 'biweekly', 'monthly'])
    )
    
    topics = fields.List(
        fields.Str(validate=validate.OneOf([
            'academic_tips',
            'writing_guides',
            'discounts',
            'company_news',
            'success_stories',
            'industry_news'
        ])),
        required=False,
        allow_none=True
    )
    
    format = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.OneOf(['html', 'text'])
    )
    
    @post_load
    def set_defaults(self, data, **kwargs):
        """Set default values."""
        data.setdefault('frequency', 'weekly')
        data.setdefault('topics', [])
        data.setdefault('format', 'html')
        return data


class NewsletterTokenSchema(Schema):
    """Validation schema for newsletter token-based operations."""
    
    token = fields.Str(
        required=True,
        validate=validate.Length(min=20, max=200),
        error_messages={'required': 'Token is required'}
    )
