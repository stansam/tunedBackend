"""
Settings schemas package.

Exports all validation schemas for user settings and preferences.
"""

# Profile schemas
from tuned.client.schemas.settings.profile import UpdateProfilePictureSchema, UpdateProfileSchema, DeleteProfilePictureSchema, ChangeEmailSchema, ChangePasswordSchema

# Preference schemas (modular)
from tuned.client.schemas.settings.notification_preferences import NotificationPreferencesSchema
from tuned.client.schemas.settings.email_preferences import EmailPreferencesSchema
from tuned.client.schemas.settings.privacy_settings import PrivacySettingsSchema
from tuned.client.schemas.settings.localization import LocalizationSettingsSchema
from tuned.client.schemas.settings.language_preferences import LanguagePreferenceSchema
from tuned.client.schemas.settings.accessibility import AccessibilityPreferencesSchema
from tuned.client.schemas.settings.billing import BillingPreferencesSchema

# Newsletter schemas
from tuned.client.schemas.settings.newsletter import (
    NewsletterSubscribeSchema,
    NewsletterUnsubscribeSchema
)

__all__ = [
    # Profile
    'UpdateProfileSchema',
    'UpdateProfilePictureSchema',
    'DeleteProfilePictureSchema',
    'ChangePasswordSchema'
    # Preferences
    'NotificationPreferencesSchema',
    'EmailPreferencesSchema',
    'PrivacySettingsSchema',
    'LocalizationSettingsSchema',
    'LanguagePreferenceSchema',  
    'AccessibilityPreferencesSchema',
    'BillingPreferencesSchema',
    # Newsletter
    'NewsletterSubscribeSchema',
    'NewsletterUnsubscribeSchema',
]
