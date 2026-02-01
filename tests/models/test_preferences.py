"""
Tests for preference models.

Tests all 6 preference models, relationships, and serialization.
"""

import pytest
from datetime import datetime, timezone
from tuned.models.user import User
from tuned.models.preferences import (
    UserNotificationPreferences,
    UserEmailPreferences,
    UserPrivacySettings,
    UserLocalizationSettings,
    UserAccessibilityPreferences,
    UserBillingPreferences
)
from tuned.models.enums import (
    EmailFrequency,
    ProfileVisibility,
    DateFormat,
    TimeFormat,
    NumberFormat,
    WeekStart,
    InvoiceDeliveryMethod
)


class TestUserNotificationPreferences:
    """Tests for UserNotificationPreferences model."""
    
    def test_create_notification_preferences(self, db_session, test_user):
        """Test creating notification preferences."""
        prefs = UserNotificationPreferences(
            user_id=test_user.id,
            email_notifications=True,
            push_notifications=True,
            order_updates=True
        )
        db_session.add(prefs)
        db_session.commit()
        
        assert prefs.id is not None
        assert prefs.user_id == test_user.id
        assert prefs.email_notifications is True
        assert prefs.created_at is not None
    
    def test_notification_preferences_defaults(self, db_session, test_user):
        """Test default values for notification preferences."""
        prefs = UserNotificationPreferences(user_id=test_user.id)
        db_session.add(prefs)
        db_session.commit()
        
        assert prefs.email_notifications is True
        assert prefs.sms_notifications is False
        assert prefs.push_notifications is True
        assert prefs.marketing_emails is False
    
    def test_notification_preferences_to_dict(self, db_session, test_user):
        """Test serialization to dictionary."""
        prefs = UserNotificationPreferences(user_id=test_user.id)
        db_session.add(prefs)
        db_session.commit()
        
        data = prefs.to_dict()
        
        assert isinstance(data, dict)
        assert data['user_id'] == test_user.id
        assert 'email_notifications' in data
        assert 'created_at' in data
        assert 'id' not in data  # Should exclude id
    
    def test_notification_preferences_cascade_delete(self, db_session, test_user):
        """Test CASCADE delete when user is deleted."""
        prefs = UserNotificationPreferences(user_id=test_user.id)
        db_session.add(prefs)
        db_session.commit()
        
        pref_id = prefs.id
        
        # Delete user
        db_session.delete(test_user)
        db_session.commit()
        
        # Preferences should be deleted
        deleted_prefs = db_session.query(UserNotificationPreferences).get(pref_id)
        assert deleted_prefs is None


class TestUserEmailPreferences:
    """Tests for UserEmailPreferences model."""
    
    def test_create_email_preferences(self, db_session, test_user):
        """Test creating email preferences."""
        prefs = UserEmailPreferences(
            user_id=test_user.id,
            newsletter=False,
            order_confirmations=True,
            frequency=EmailFrequency.INSTANT
        )
        db_session.add(prefs)
        db_session.commit()
        
        assert prefs.id is not None
        assert prefs.frequency == EmailFrequency.INSTANT
    
    def test_email_preferences_critical_defaults(self, db_session, test_user):
        """Test that critical emails default to True."""
        prefs = UserEmailPreferences(user_id=test_user.id)
        db_session.add(prefs)
        db_session.commit()
        
        # Critical emails should default to True
        assert prefs.order_confirmations is True
        assert prefs.payment_receipts is True
        assert prefs.account_security is True


class TestUserPrivacySettings:
    """Tests for UserPrivacySettings model."""
    
    def test_create_privacy_settings(self, db_session, test_user):
        """Test creating privacy settings."""
        settings = UserPrivacySettings(
            user_id=test_user.id,
            profile_visibility=ProfileVisibility.PRIVATE,
            show_email=False
        )
        db_session.add(settings)
        db_session.commit()
        
        assert settings.id is not None
        assert settings.profile_visibility == ProfileVisibility.PRIVATE
    
    def test_privacy_settings_defaults(self, db_session, test_user):
        """Test default privacy settings are secure."""
        settings = UserPrivacySettings(user_id=test_user.id)
        db_session.add(settings)
        db_session.commit()
        
        # Secure defaults
        assert settings.profile_visibility == ProfileVisibility.PRIVATE
        assert settings.show_email is False
        assert settings.show_phone is False
        assert settings.data_sharing is False


class TestUserLocalizationSettings:
    """Tests for UserLocalizationSettings model."""
    
    def test_create_localization_settings(self, db_session, test_user):
        """Test creating localization settings."""
        settings = UserLocalizationSettings(
            user_id=test_user.id,
            language='es',
            timezone='America/New_York',
            date_format=DateFormat.DD_MM_YYYY,
            time_format=TimeFormat.TWENTYFOUR_HOUR
        )
        db_session.add(settings)
        db_session.commit()
        
        assert settings.language == 'es'
        assert settings.timezone == 'America/New_York'
        assert settings.date_format == DateFormat.DD_MM_YYYY
    
    def test_localization_defaults(self, db_session, test_user):
        """Test default localization settings."""
        settings = UserLocalizationSettings(user_id=test_user.id)
        db_session.add(settings)
        db_session.commit()
        
        assert settings.language == 'en'
        assert settings.timezone == 'UTC'
        assert settings.date_format == DateFormat.MM_DD_YYYY


class TestUserAccessibilityPreferences:
    """Tests for UserAccessibilityPreferences model."""
    
    def test_create_accessibility_preferences(self, db_session, test_user):
        """Test creating accessibility preferences."""
        prefs = UserAccessibilityPreferences(
            user_id=test_user.id,
            font_size_multiplier=1.5,
            high_contrast_mode=True,
            reduced_motion=True
        )
        db_session.add(prefs)
        db_session.commit()
        
        assert prefs.font_size_multiplier == 1.5
        assert prefs.high_contrast_mode is True
    
    def test_accessibility_defaults(self, db_session, test_user):
        """Test accessibility defaults are disabled."""
        prefs = UserAccessibilityPreferences(user_id=test_user.id)
        db_session.add(prefs)
        db_session.commit()
        
        assert prefs.font_size_multiplier == 1.0
        assert prefs.high_contrast_mode is False
        assert prefs.reduced_motion is False


class TestUserBillingPreferences:
    """Tests for UserBillingPreferences model."""
    
    def test_create_billing_preferences(self, db_session, test_user):
        """Test creating billing preferences."""
        prefs = UserBillingPreferences(
            user_id=test_user.id,
            invoice_email='billing@example.com',
            invoice_delivery=InvoiceDeliveryMethod.EMAIL,
            payment_reminders=True
        )
        db_session.add(prefs)
        db_session.commit()
        
        assert prefs.invoice_email == 'billing@example.com'
        assert prefs.invoice_delivery == InvoiceDeliveryMethod.EMAIL
    
    def test_billing_defaults(self, db_session, test_user):
        """Test billing preference defaults."""
        prefs = UserBillingPreferences(user_id=test_user.id)
        db_session.add(prefs)
        db_session.commit()
        
        assert prefs.invoice_delivery == InvoiceDeliveryMethod.EMAIL
        assert prefs.payment_reminders is True
        assert prefs.reminder_days_before == 3


class TestPreferenceRelationships:
    """Tests for preference model relationships with User."""
    
    def test_user_has_all_preferences(self, db_session, test_user):
        """Test that user can access all preference backref."""
        # Create all preferences
        UserNotificationPreferences(user_id=test_user.id)
        UserEmailPreferences(user_id=test_user.id)
        UserPrivacySettings(user_id=test_user.id)
        UserLocalizationSettings(user_id=test_user.id)
        UserAccessibilityPreferences(user_id=test_user.id)
        UserBillingPreferences(user_id=test_user.id)
        db_session.commit()
        
        # Access via backref
        assert test_user.notification_preferences is not None
        assert test_user.email_preferences is not None
        assert test_user.privacy_settings is not None
        assert test_user.localization_settings is not None
        assert test_user.accessibility_preferences is not None
        assert test_user.billing_preferences is not None
    
    def test_preference_unique_constraint(self, db_session, test_user):
        """Test that only one preference per user is allowed."""
        prefs1 = UserNotificationPreferences(user_id=test_user.id)
        db_session.add(prefs1)
        db_session.commit()
        
        # Try to create duplicate
        prefs2 = UserNotificationPreferences(user_id=test_user.id)
        db_session.add(prefs2)
        
        with pytest.raises(Exception):  # Should raise IntegrityError
            db_session.commit()
