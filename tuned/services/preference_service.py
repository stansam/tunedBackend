"""
Preference service module.

Centralized service for managing user preferences across all categories.
Provides initialization, retrieval, export, import, and reset functionality.
"""

from datetime import datetime, timezone
from typing import Dict, Optional, List
from flask import current_app
from tuned.extensions import db
from tuned.models.user import User
from tuned.models.preferences import (
    UserNotificationPreferences,
    UserEmailPreferences,
    UserPrivacySettings,
    UserLocalizationSettings,
    UserAccessibilityPreferences,
    UserBillingPreferences
)
from tuned.models.audit import ActivityLog
import logging


logger = logging.getLogger(__name__)


def initialize_user_preferences(user_id: int) -> Dict[str, bool]:
    """
    Initialize all preference models for a new user with defaults.
    
    Creates all 6 preference categories if they don't already exist.
    This function is idempotent - safe to call multiple times.
    
    Args:
        user_id: ID of the user to initialize preferences for
        
    Returns:
        dict: Status of initialization for each category
        Example: {
            'notification': True,
            'email': True,
            'privacy': True,
            'localization': True,
            'accessibility': True,
            'billing': True,
            'success': True
        }
    """
    result = {}
    user = User.query.get(user_id)
    
    if not user:
        logger.error(f"Cannot initialize preferences: User {user_id} not found")
        return {'success': False, 'error': 'User not found'}
    
    try:
        # 1. Notification Preferences
        if not user.notification_preferences:
            notif_prefs = UserNotificationPreferences(user_id=user_id)
            db.session.add(notif_prefs)
            result['notification'] = True
        else:
            result['notification'] = False  # Already exists
        
        # 2. Email Preferences
        if not user.email_preferences:
            email_prefs = UserEmailPreferences(user_id=user_id)
            db.session.add(email_prefs)
            result['email'] = True
        else:
            result['email'] = False
        
        # 3. Privacy Settings
        if not user.privacy_settings:
            privacy_settings = UserPrivacySettings(user_id=user_id)
            db.session.add(privacy_settings)
            result['privacy'] = True
        else:
            result['privacy'] = False
        
        # 4. Localization Settings (use User.language and User.timezone if set)
        if not user.localization_settings:
            localization = UserLocalizationSettings(
                user_id=user_id,
                language=user.language or 'en',
                timezone=user.timezone or 'UTC'
            )
            db.session.add(localization)
            result['localization'] = True
        else:
            result['localization'] = False
        
        # 5. Accessibility Preferences
        if not user.accessibility_preferences:
            accessibility = UserAccessibilityPreferences(user_id=user_id)
            db.session.add(accessibility)
            result['accessibility'] = True
        else:
            result['accessibility'] = False
        
        # 6. Billing Preferences
        if not user.billing_preferences:
            billing = UserBillingPreferences(user_id=user_id)
            db.session.add(billing)
            result['billing'] = True
        else:
            result['billing'] = False
        
        db.session.commit()
        
        result['success'] = True
        logger.info(f"Initialized preferences for user {user_id}: {result}")
        
        return result
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to initialize preferences for user {user_id}: {str(e)}")
        return {'success': False, 'error': str(e)}


def get_all_user_preferences(user_id: int, lazy_init: bool = True) -> Optional[Dict]:
    """
    Retrieve all preferences for a user across all categories.
    
    Args:
        user_id: ID of the user
        lazy_init: If True, initialize missing preferences automatically
        
    Returns:
        dict: All preferences organized by category, or None if user not found
        Example: {
            'notification': {...},
            'email': {...},
            'privacy': {...},
            'localization': {...},
            'accessibility': {...},
            'billing': {...}
        }
    """
    user = User.query.get(user_id)
    
    if not user:
        logger.warning(f"User {user_id} not found")
        return None
    
    # Lazy initialization if any preferences are missing
    if lazy_init:
        needs_init = (
            not user.notification_preferences or
            not user.email_preferences or
            not user.privacy_settings or
            not user.localization_settings or
            not user.accessibility_preferences or
            not user.billing_preferences
        )
        
        if needs_init:
            logger.info(f"Lazy-initializing missing preferences for user {user_id}")
            initialize_user_preferences(user_id)
            # Refresh user object to get new preferences
            db.session.refresh(user)
    
    return {
        'notification': user.notification_preferences.to_dict() if user.notification_preferences else None,
        'email': user.email_preferences.to_dict() if user.email_preferences else None,
        'privacy': user.privacy_settings.to_dict() if user.privacy_settings else None,
        'localization': user.localization_settings.to_dict() if user.localization_settings else None,
        'accessibility': user.accessibility_preferences.to_dict() if user.accessibility_preferences else None,
        'billing': user.billing_preferences.to_dict() if user.billing_preferences else None
    }


def export_user_preferences(user_id: int) -> Optional[Dict]:
    """
    Export all user preferences in a GDPR-compliant format.
    
    Returns all preference data in a structured format for data portability.
    Does NOT include sensitive data like passwords or tokens.
    
    Args:
        user_id: ID of the user
        
    Returns:
        dict: Complete preference export with metadata
    """
    user = User.query.get(user_id)
    
    if not user:
        return None
    
    preferences = get_all_user_preferences(user_id, lazy_init=True)
    
    export_data = {
        'export_metadata': {
            'user_id': user_id,
            'username': user.username,
            'email': user.email,
            'export_date': datetime.now(timezone.utc).isoformat(),
            'data_version': '1.0'
        },
        'preferences': preferences,
        'user_info': {
            'language': user.language,
            'timezone': user.timezone,
            'created_at': user.created_at.isoformat() if user.created_at else None
        }
    }
    
    # Log export activity
    try:
        activity = ActivityLog(
            user_id=user_id,
            action='preference_data_exported',
            entity_type='User',
            entity_id=user_id,
            details={'export_timestamp': datetime.now(timezone.utc).isoformat()}
        )
        db.session.add(activity)
        db.session.commit()
    except Exception as e:
        logger.error(f"Failed to log preference export for user {user_id}: {str(e)}")
    
    logger.info(f"Exported preferences for user {user_id}")
    return export_data


def import_user_preferences(user_id: int, import_data: Dict) -> Dict[str, any]:
    """
    Import user preferences from export data (GDPR data portability).
    
    Validates and safely imports preference data. Does NOT allow
    privilege escalation or modification of critical system fields.
    
    Args:
        user_id: ID of the user
        import_data: Dictionary containing preference data to import
        
    Returns:
        dict: Result of import with validation errors if any
    """
    user = User.query.get(user_id)
    
    if not user:
        return {'success': False, 'error': 'User not found'}
    
    validation_errors = []
    imported_categories = []
    
    try:
        preferences_data = import_data.get('preferences', {})
        
        # Import each category if data is provided
        if 'notification' in preferences_data and preferences_data['notification']:
            if user.notification_preferences:
                # Update existing
                for key, value in preferences_data['notification'].items():
                    if hasattr(user.notification_preferences, key) and key not in ['id', 'user_id', 'created_at']:
                        setattr(user.notification_preferences, key, value)
                imported_categories.append('notification')
        
        if 'email' in preferences_data and preferences_data['email']:
            if user.email_preferences:
                for key, value in preferences_data['email'].items():
                    # Enforce critical email protection
                    if key in ['order_confirmations', 'payment_receipts', 'account_security']:
                        if value is False:
                            validation_errors.append(f"Cannot disable critical email: {key}")
                            continue
                    if hasattr(user.email_preferences, key) and key not in ['id', 'user_id', 'created_at']:
                        setattr(user.email_preferences, key, value)
                imported_categories.append('email')
        
        if 'privacy' in preferences_data and preferences_data['privacy']:
            if user.privacy_settings:
                for key, value in preferences_data['privacy'].items():
                    if hasattr(user.privacy_settings, key) and key not in ['id', 'user_id', 'created_at']:
                        setattr(user.privacy_settings, key, value)
                imported_categories.append('privacy')
        
        if 'localization' in preferences_data and preferences_data['localization']:
            if user.localization_settings:
                for key, value in preferences_data['localization'].items():
                    if hasattr(user.localization_settings, key) and key not in ['id', 'user_id', 'created_at']:
                        setattr(user.localization_settings, key, value)
                imported_categories.append('localization')
        
        if 'accessibility' in preferences_data and preferences_data['accessibility']:
            if user.accessibility_preferences:
                for key, value in preferences_data['accessibility'].items():
                    if hasattr(user.accessibility_preferences, key) and key not in ['id', 'user_id', 'created_at']:
                        setattr(user.accessibility_preferences, key, value)
                imported_categories.append('accessibility')
        
        if 'billing' in preferences_data and preferences_data['billing']:
            if user.billing_preferences:
                for key, value in preferences_data['billing'].items():
                    if hasattr(user.billing_preferences, key) and key not in ['id', 'user_id', 'created_at']:
                        setattr(user.billing_preferences, key, value)
                imported_categories.append('billing')
        
        db.session.commit()
        
        # Log import activity
        activity = ActivityLog(
            user_id=user_id,
            action='preference_data_imported',
            entity_type='User',
            entity_id=user_id,
            details={
                'imported_categories': imported_categories,
                'validation_errors': validation_errors
            }
        )
        db.session.add(activity)
        db.session.commit()
        
        logger.info(f"Imported preferences for user {user_id}: {imported_categories}")
        
        return {
            'success': True,
            'imported_categories': imported_categories,
            'validation_errors': validation_errors
        }
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to import preferences for user {user_id}: {str(e)}")
        return {'success': False, 'error': str(e)}


def reset_preferences_to_defaults(user_id: int, category: Optional[str] = None) -> Dict[str, any]:
    """
    Reset user preferences to default values.
    
    Can reset a specific category or all categories at once.
    Creates a snapshot before resetting for potential recovery.
    
    Args:
        user_id: ID of the user
        category: Specific category to reset (notification, email, privacy, etc.)
                 If None, resets all categories
                 
    Returns:
        dict: Result of reset operation
    """
    user = User.query.get(user_id)
    
    if not user:
        return {'success': False, 'error': 'User not found'}
    
    try:
        # Create snapshot before reset (for potential recovery)
        snapshot = export_user_preferences(user_id)
        
        reset_categories = []
        
        if category is None or category == 'notification':
            if user.notification_preferences:
                db.session.delete(user.notification_preferences)
                reset_categories.append('notification')
        
        if category is None or category == 'email':
            if user.email_preferences:
                db.session.delete(user.email_preferences)
                reset_categories.append('email')
        
        if category is None or category == 'privacy':
            if user.privacy_settings:
                db.session.delete(user.privacy_settings)
                reset_categories.append('privacy')
        
        if category is None or category == 'localization':
            if user.localization_settings:
                db.session.delete(user.localization_settings)
                reset_categories.append('localization')
        
        if category is None or category == 'accessibility':
            if user.accessibility_preferences:
                db.session.delete(user.accessibility_preferences)
                reset_categories.append('accessibility')
        
        if category is None or category == 'billing':
            if user.billing_preferences:
                db.session.delete(user.billing_preferences)
                reset_categories.append('billing')
        
        db.session.commit()
        
        # Re-initialize with defaults
        initialize_user_preferences(user_id)
        
        # Log reset activity
        activity = ActivityLog(
            user_id=user_id,
            action='preferences_reset',
            entity_type='User',
            entity_id=user_id,
            details={
                'reset_categories': reset_categories,
                'snapshot_created': True
            }
        )
        db.session.add(activity)
        db.session.commit()
        
        logger.info(f"Reset preferences for user {user_id}: {reset_categories}")
        
        return {
            'success': True,
            'reset_categories': reset_categories,
            'snapshot': snapshot
        }
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to reset preferences for user {user_id}: {str(e)}")
        return {'success': False, 'error': str(e)}
