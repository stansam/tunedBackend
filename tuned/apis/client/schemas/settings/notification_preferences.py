"""
Validation schema for user notification preferences.

Handles validation for notification settings including channels
(email, SMS, push) and categories (orders, payments, delivery, etc.).
"""

from marshmallow import Schema, fields, post_load


class NotificationPreferencesSchema(Schema):
    """Validation schema for notification preferences."""
    
    # Channels
    email_notifications = fields.Boolean(required=False, allow_none=True)
    sms_notifications = fields.Boolean(required=False, allow_none=True)
    push_notifications = fields.Boolean(required=False, allow_none=True)
    
    # Categories
    order_updates = fields.Boolean(required=False, allow_none=True)
    payment_notifications = fields.Boolean(required=False, allow_none=True)
    delivery_notifications = fields.Boolean(required=False, allow_none=True)
    revision_updates = fields.Boolean(required=False, allow_none=True)
    extension_updates = fields.Boolean(required=False, allow_none=True)
    comment_notifications = fields.Boolean(required=False, allow_none=True)
    support_ticket_updates = fields.Boolean(required=False, allow_none=True)
    marketing_emails = fields.Boolean(required=False, allow_none=True)
    weekly_summary = fields.Boolean(required=False, allow_none=True)
    
    @post_load
    def set_defaults(self, data, **kwargs):
        """Set default values for notification preferences."""
        data.setdefault('email_notifications', True)
        data.setdefault('sms_notifications', False)
        data.setdefault('push_notifications', True)
        data.setdefault('order_updates', True)
        data.setdefault('payment_notifications', True)
        data.setdefault('delivery_notifications', True)
        data.setdefault('revision_updates', True)
        data.setdefault('extension_updates', True)
        data.setdefault('marketing_emails', False)
        data.setdefault('weekly_summary', False)
        data.setdefault('comment_notifications', True)
        data.setdefault('support_ticket_updates', True)
        return data
