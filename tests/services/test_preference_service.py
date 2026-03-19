"""
Tests for preference service layer.

Tests all preference_service functions including initialization,
retrieval, export, import, and reset.
"""

import pytest
from tuned.services.preference_service import (
    initialize_user_preferences,
    get_all_user_preferences,
    export_user_preferences,
    import_user_preferences,
    reset_preferences_to_defaults
)
from tuned.models.user import User
from tuned.models.preferences import (
    UserNotificationPreferences,
    UserEmailPreferences,
    UserPrivacySettings
)


class TestInitializeUserPreferences:
    """Tests for initialize_user_preferences function."""
    
    def test_initialize_creates_all_preferences(self, db_session, test_user):
        """Test that initialization creates all 6 preference categories."""
        result = initialize_user_preferences(test_user.id)
        
        assert result['success'] is True
        assert result['notification'] is True
        assert result['email'] is True
        assert result['privacy'] is True
        assert result['localization'] is True
        assert result['accessibility'] is True
        assert result['billing'] is True
        
        # Verify preferences exist in database
        user = User.query.get(test_user.id)
        assert user.notification_preferences is not None
        assert user.email_preferences is not None
        assert user.privacy_settings is not None
        assert user.localization_settings is not None
        assert user.accessibility_preferences is not None
        assert user.billing_preferences is not None
    
    def test_initialize_is_idempotent(self, db_session, test_user):
        """Test that initialization can be called multiple times safely."""
        # First initialization
        result1 = initialize_user_preferences(test_user.id)
        assert result1['success'] is True
        assert result1['notification'] is True
        
        # Second initialization
        result2 = initialize_user_preferences(test_user.id)
        assert result2['success'] is True
        assert result2['notification'] is False  # Already exists
    
    def test_initialize_uses_user_language_timezone(self, db_session, test_user):
        """Test that localization uses User.language and User.timezone if set."""
        test_user.language = 'es'
        test_user.timezone = 'America/New_York'
        db_session.commit()
        
        initialize_user_preferences(test_user.id)
        
        user = User.query.get(test_user.id)
        assert user.localization_settings.language == 'es'
        assert user.localization_settings.timezone == 'America/New_York'
    
    def test_initialize_nonexistent_user(self, db_session):
        """Test initialization with non-existent user."""
        result = initialize_user_preferences(99999)
        
        assert result['success'] is False
        assert 'error' in result


class TestGetAllUserPreferences:
    """Tests for get_all_user_preferences function."""
    
    def test_get_all_preferences(self, db_session, test_user):
        """Test retrieving all preferences."""
        initialize_user_preferences(test_user.id)
        
        prefs = get_all_user_preferences(test_user.id, lazy_init=False)
        
        assert prefs is not None
        assert 'notification' in prefs
        assert 'email' in prefs
        assert 'privacy' in prefs
        assert 'localization' in prefs
        assert 'accessibility' in prefs
        assert 'billing' in prefs
    
    def test_get_all_with_lazy_init(self, db_session, test_user):
        """Test lazy initialization when preferences don't exist."""
        # Don't initialize preferences first
        prefs = get_all_user_preferences(test_user.id, lazy_init=True)
        
        assert prefs is not None
        # Preferences should be created automatically
        user = User.query.get(test_user.id)
        assert user.notification_preferences is not None
    
    def test_get_all_nonexistent_user(self, db_session):
        """Test getting preferences for non-existent user."""
        prefs = get_all_user_preferences(99999)
        
        assert prefs is None


class TestExportUserPreferences:
    """Tests for export_user_preferences function (GDPR compliance)."""
    
    def test_export_creates_complete_data(self, db_session, test_user):
        """Test that export creates complete GDPR-compliant data."""
        initialize_user_preferences(test_user.id)
        
        export = export_user_preferences(test_user.id)
        
        assert export is not None
        assert 'export_metadata' in export
        assert 'preferences' in export
        assert 'user_info' in export
        
        # Check metadata
        metadata = export['export_metadata']
        assert metadata['user_id'] == test_user.id
        assert metadata['username'] == test_user.username
        assert metadata['email'] == test_user.email
        assert 'export_date' in metadata
        
        # Check preferences
        prefs = export['preferences']
        assert prefs['notification'] is not None
        assert prefs['email'] is not None
    
    def test_export_nonexistent_user(self, db_session):
        """Test export for non-existent user."""
        export = export_user_preferences(99999)
        
        assert export is None


class TestImportUserPreferences:
    """Tests for import_user_preferences function (GDPR compliance)."""
    
    def test_import_valid_data(self, db_session, test_user):
        """Test importing valid preference data."""
        initialize_user_preferences(test_user.id)
        
        # Create import data
        import_data = {
            'preferences': {
                'notification': {
                    'email_notifications': False,
                    'sms_notifications': True
                },
                'email': {
                    'newsletter': True,
                    'promotional_emails': True
                }
            }
        }
        
        result = import_user_preferences(test_user.id, import_data)
        
        assert result['success'] is True
        assert 'notification' in result['imported_categories']
        assert 'email' in result['imported_categories']
        
        # Verify changes
        user = User.query.get(test_user.id)
        assert user.notification_preferences.email_notifications is False
        assert user.email_preferences.newsletter is True
    
    def test_import_critical_email_protection(self, db_session, test_user):
        """Test that critical emails cannot be disabled via import."""
        initialize_user_preferences(test_user.id)
        
        import_data = {
            'preferences': {
                'email': {
                    'order_confirmations': False,  # Try to disable
                    'payment_receipts': False,
                    'account_security': False
                }
            }
        }
        
        result = import_user_preferences(test_user.id, import_data)
        
        # Should have validation errors
        assert len(result['validation_errors']) > 0
        
        # Critical emails should remain True
        user = User.query.get(test_user.id)
        assert user.email_preferences.order_confirmations is True
        assert user.email_preferences.payment_receipts is True
        assert user.email_preferences.account_security is True
    
    def test_import_nonexistent_user(self, db_session):
        """Test import for non-existent user."""
        import_data = {'preferences': {}}
        result = import_user_preferences(99999, import_data)
        
        assert result['success'] is False


class TestResetPreferencesToDefaults:
    """Tests for reset_preferences_to_defaults function."""
    
    def test_reset_all_categories(self, db_session, test_user):
        """Test resetting all preference categories."""
        initialize_user_preferences(test_user.id)
        
        # Modify some preferences
        user = User.query.get(test_user.id)
        user.notification_preferences.email_notifications = False
        user.email_preferences.newsletter = True
        db_session.commit()
        
        # Reset all
        result = reset_preferences_to_defaults(test_user.id, category=None)
        
        assert result['success'] is True
        assert len(result['reset_categories']) == 6
        assert 'snapshot' in result
        
        # Verify defaults restored
        db_session.refresh(user)
        assert user.notification_preferences.email_notifications is True
        assert user.email_preferences.newsletter is False
    
    def test_reset_single_category(self, db_session, test_user):
        """Test resetting a single category."""
        initialize_user_preferences(test_user.id)
        
        # Modify notification preferences
        user = User.query.get(test_user.id)
        user.notification_preferences.email_notifications = False
        user.email_preferences.newsletter = True
        db_session.commit()
        
        # Reset only notification
        result = reset_preferences_to_defaults(test_user.id, category='notification')
        
        assert result['success'] is True
        assert result['reset_categories'] == ['notification']
        
        # Verify notification reset but email unchanged
        db_session.refresh(user)
        assert user.notification_preferences.email_notifications is True
        assert user.email_preferences.newsletter is True  # Unchanged
    
    def test_reset_creates_snapshot(self, db_session, test_user):
        """Test that reset creates snapshot for recovery."""
        initialize_user_preferences(test_user.id)
        
        result = reset_preferences_to_defaults(test_user.id)
        
        assert 'snapshot' in result
        snapshot = result['snapshot']
        
        assert snapshot is not None
        assert 'export_metadata' in snapshot
        assert 'preferences' in snapshot
    
    def test_reset_nonexistent_user(self, db_session):
        """Test reset for non-existent user."""
        result = reset_preferences_to_defaults(99999)
        
        assert result['success'] is False
