from marshmallow import Schema, fields, validate

class LocalizationUpdateSchema(Schema):
    language = fields.Str(validate=validate.Length(min=2, max=10))
    country_code = fields.Str(allow_none=True, validate=validate.Length(equal=2))
    timezone = fields.Str()
    date_format = fields.Str()
    time_format = fields.Str()
    currency = fields.Str(validate=validate.Length(equal=3))
    number_format = fields.Str()
    week_start = fields.Str()

class NotificationUpdateSchema(Schema):
    email_notifications = fields.Bool()
    sms_notifications = fields.Bool()
    push_notifications = fields.Bool()
    order_updates = fields.Bool()
    payment_notifications = fields.Bool()
    delivery_notifications = fields.Bool()
    revision_updates = fields.Bool()
    extension_updates = fields.Bool()
    comment_notifications = fields.Bool()
    support_ticket_updates = fields.Bool()
    marketing_emails = fields.Bool()
    weekly_summary = fields.Bool()

class EmailPreferenceUpdateSchema(Schema):
    newsletter = fields.Bool()
    promotional_emails = fields.Bool()
    product_updates = fields.Bool()
    frequency = fields.Str()
    daily_digest_hour = fields.Int(allow_none=True, validate=validate.Range(min=0, max=23))

class PrivacyUpdateSchema(Schema):
    profile_visibility = fields.Str()
    show_email = fields.Bool()
    show_phone = fields.Bool()
    show_name = fields.Bool()
    allow_messages = fields.Bool()
    allow_comments = fields.Bool()
    data_sharing = fields.Bool()
    analytics_tracking = fields.Bool()
    third_party_cookies = fields.Bool()
    allow_search_engine_indexing = fields.Bool()

class AccessibilityUpdateSchema(Schema):
    font_size_multiplier = fields.Float(validate=validate.Range(min=0.8, max=2.0))
    text_spacing_increased = fields.Bool()
    high_contrast_mode = fields.Bool()
    color_blind_mode = fields.Bool()
    reduced_motion = fields.Bool()
    screen_reader_optimized = fields.Bool()
    keyboard_navigation_enhanced = fields.Bool()
    focus_indicators_enhanced = fields.Bool()

class BillingPreferenceUpdateSchema(Schema):
    invoice_email = fields.Email(allow_none=True)
    invoice_delivery = fields.Str()
    payment_reminders = fields.Bool()
    reminder_days_before = fields.Int(validate=validate.Range(min=1, max=30))
    auto_reload_enabled = fields.Bool(allow_none=True)
    auto_reload_threshold = fields.Float(allow_none=True)
