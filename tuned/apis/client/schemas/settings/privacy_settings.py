"""
Validation schema for user privacy settings.

Handles validation for profile visibility, data sharing,
and communication preferences.
"""

from marshmallow import Schema, fields, validate, post_load


class PrivacySettingsSchema(Schema):
    """Validation schema for privacy settings."""
    
    profile_visibility = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.OneOf(['public', 'private', 'friends_only'])
    )
    
    show_email = fields.Boolean(required=False, allow_none=True)
    show_phone = fields.Boolean(required=False, allow_none=True)
    show_name = fields.Boolean(required=False, allow_none=True)
    allow_messages = fields.Boolean(required=False, allow_none=True)
    allow_comments = fields.Boolean(required=False, allow_none=True)
    data_sharing = fields.Boolean(required=False, allow_none=True)
    analytics_tracking = fields.Boolean(required=False, allow_none=True)
    third_party_cookies = fields.Boolean(required=False, allow_none=True)
    allow_search_engine_indexing = fields.Boolean(required=False, allow_none=True)
    
    @post_load
    def set_defaults(self, data, **kwargs):
        """Set default values for privacy settings."""
        data.setdefault('profile_visibility', 'private')
        data.setdefault('show_email', False)
        data.setdefault('show_phone', False)
        data.setdefault('show_name', True)
        data.setdefault('allow_messages', True)
        data.setdefault('allow_comments', True)
        data.setdefault('data_sharing', False)
        data.setdefault('analytics_tracking', True)
        data.setdefault('third_party_cookies', False)
        data.setdefault('allow_search_engine_indexing', False)
        return data
