from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any
from datetime import datetime

@dataclass
class LocalizationDTO:
    language: str
    country_code: Optional[str]
    timezone: str
    date_format: str
    time_format: str
    currency: str
    number_format: str
    week_start: str

    @classmethod
    def from_model(cls, obj) -> "LocalizationDTO":
        return cls(
            language=obj.language,
            country_code=obj.country_code,
            timezone=obj.timezone,
            date_format=obj.date_format.value if hasattr(obj.date_format, 'value') else obj.date_format,
            time_format=obj.time_format.value if hasattr(obj.time_format, 'value') else obj.time_format,
            currency=obj.currency,
            number_format=obj.number_format.value if hasattr(obj.number_format, 'value') else obj.number_format,
            week_start=obj.week_start.value if hasattr(obj.week_start, 'value') else obj.week_start
        )

@dataclass
class NotificationDTO:
    email_notifications: bool
    sms_notifications: bool
    push_notifications: bool
    order_updates: bool
    payment_notifications: bool
    delivery_notifications: bool
    revision_updates: bool
    extension_updates: bool
    comment_notifications: bool
    support_ticket_updates: bool
    marketing_emails: bool
    weekly_summary: bool

    @classmethod
    def from_model(cls, obj) -> "NotificationDTO":
        return cls(
            email_notifications=obj.email_notifications,
            sms_notifications=obj.sms_notifications,
            push_notifications=obj.push_notifications,
            order_updates=obj.order_updates,
            payment_notifications=obj.payment_notifications,
            delivery_notifications=obj.delivery_notifications,
            revision_updates=obj.revision_updates,
            extension_updates=obj.extension_updates,
            comment_notifications=obj.comment_notifications,
            support_ticket_updates=obj.support_ticket_updates,
            marketing_emails=obj.marketing_emails,
            weekly_summary=obj.weekly_summary
        )

@dataclass
class EmailPreferenceDTO:
    newsletter: bool
    promotional_emails: bool
    product_updates: bool
    order_confirmations: bool
    payment_receipts: bool
    account_security: bool
    frequency: str
    daily_digest_hour: Optional[int]

    @classmethod
    def from_model(cls, obj) -> "EmailPreferenceDTO":
        return cls(
            newsletter=obj.newsletter,
            promotional_emails=obj.promotional_emails,
            product_updates=obj.product_updates,
            order_confirmations=obj.order_confirmations,
            payment_receipts=obj.payment_receipts,
            account_security=obj.account_security,
            frequency=obj.frequency.value if hasattr(obj.frequency, 'value') else obj.frequency,
            daily_digest_hour=obj.daily_digest_hour
        )

@dataclass
class PrivacyDTO:
    profile_visibility: str
    show_email: bool
    show_phone: bool
    show_name: bool
    allow_messages: bool
    allow_comments: bool
    data_sharing: bool
    analytics_tracking: bool
    third_party_cookies: bool
    allow_search_engine_indexing: bool

    @classmethod
    def from_model(cls, obj) -> "PrivacyDTO":
        return cls(
            profile_visibility=obj.profile_visibility.value if hasattr(obj.profile_visibility, 'value') else obj.profile_visibility,
            show_email=obj.show_email,
            show_phone=obj.show_phone,
            show_name=obj.show_name,
            allow_messages=obj.allow_messages,
            allow_comments=obj.allow_comments,
            data_sharing=obj.data_sharing,
            analytics_tracking=obj.analytics_tracking,
            third_party_cookies=obj.third_party_cookies,
            allow_search_engine_indexing=obj.allow_search_engine_indexing
        )

@dataclass
class AccessibilityDTO:
    font_size_multiplier: float
    text_spacing_increased: bool
    high_contrast_mode: bool
    color_blind_mode: bool
    reduced_motion: bool
    screen_reader_optimized: bool
    keyboard_navigation_enhanced: bool
    focus_indicators_enhanced: bool

    @classmethod
    def from_model(cls, obj) -> "AccessibilityDTO":
        return cls(
            font_size_multiplier=float(obj.font_size_multiplier),
            text_spacing_increased=obj.text_spacing_increased,
            high_contrast_mode=obj.high_contrast_mode,
            color_blind_mode=obj.color_blind_mode,
            reduced_motion=obj.reduced_motion,
            screen_reader_optimized=obj.screen_reader_optimized,
            keyboard_navigation_enhanced=obj.keyboard_navigation_enhanced,
            focus_indicators_enhanced=obj.focus_indicators_enhanced
        )

@dataclass
class BillingPreferenceDTO:
    invoice_email: Optional[str]
    invoice_delivery: str
    payment_reminders: bool
    reminder_days_before: int
    auto_reload_enabled: Optional[bool]
    auto_reload_threshold: Optional[float]

    @classmethod
    def from_model(cls, obj) -> "BillingPreferenceDTO":
        return cls(
            invoice_email=obj.invoice_email,
            invoice_delivery=obj.invoice_delivery.value if hasattr(obj.invoice_delivery, 'value') else obj.invoice_delivery,
            payment_reminders=obj.payment_reminders,
            reminder_days_before=obj.reminder_days_before,
            auto_reload_enabled=obj.auto_reload_enabled,
            auto_reload_threshold=float(obj.auto_reload_threshold) if obj.auto_reload_threshold else None
        )

@dataclass
class AllPreferencesResponseDTO:
    localization: LocalizationDTO
    notification: NotificationDTO
    email: EmailPreferenceDTO
    privacy: PrivacyDTO
    accessibility: AccessibilityDTO
    billing: BillingPreferenceDTO

    def to_dict(self) -> Dict[str, Any]:
        return {
            "localization": asdict(self.localization),
            "notification": asdict(self.notification),
            "email": asdict(self.email),
            "privacy": asdict(self.privacy),
            "accessibility": asdict(self.accessibility),
            "billing": asdict(self.billing)
        }
