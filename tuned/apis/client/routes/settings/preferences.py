"""
User preferences management routes.

Provides RESTful endpoints for managing all user preferences:
- GET/PUT for each preference category
- Bulk GET/PUT for all preferences
- Export/Import for GDPR compliance
- Reset preferences to defaults
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError
from tuned.utils import success_response, error_response, validation_error_response
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
    UserPrivacySettings,
    UserLocalizationSettings,
    UserAccessibilityPreferences,
    UserBillingPreferences
)
from tuned.client.schemas.settings import (
    NotificationPreferencesSchema,
    EmailPreferencesSchema,
    PrivacySettingsSchema,
    LocalizationSettingsSchema,
    AccessibilityPreferencesSchema,
    BillingPreferencesSchema
)
from tuned.extensions import db
import logging


logger = logging.getLogger(__name__)

# Create preferences blueprint
preferences_bp = Blueprint('preferences', __name__, url_prefix='/preferences')


@preferences_bp.route('', methods=['GET'])
@jwt_required()
def get_all_preferences():
    """
    Get all user preferences across all categories.
    
    Returns:
        200: All preferences
        404: User not found
    """
    user_id = get_jwt_identity()
    
    preferences = get_all_user_preferences(user_id, lazy_init=True)
    
    if preferences is None:
        return error_response('User not found', status=404)
    
    return success_response(
        data=preferences,
        message='Preferences retrieved successfully'
    )


@preferences_bp.route('/notification', methods=['GET'])
@jwt_required()
def get_notification_preferences():
    """Get notification preferences."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return error_response('User not found', status=404)
    
    # Lazy init if missing
    if not user.notification_preferences:
        initialize_user_preferences(user_id)
        db.session.refresh(user)
    
    return success_response(
        data=user.notification_preferences.to_dict() if user.notification_preferences else None,
        message='Notification preferences retrieved'
    )


@preferences_bp.route('/notification', methods=['PUT'])
@jwt_required()
def update_notification_preferences():
    """Update notification preferences."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return error_response('User not found', status=404)
    
    try:
        schema = NotificationPreferencesSchema()
        data = schema.load(request.get_json())
    except ValidationError as err:
        return validation_error_response(err.messages)
    
    # Lazy init if missing
    if not user.notification_preferences:
        initialize_user_preferences(user_id)
        db.session.refresh(user)
    
    # Update preferences
    for key, value in data.items():
        if hasattr(user.notification_preferences, key):
            setattr(user.notification_preferences, key, value)
    
    db.session.commit()
    
    logger.info(f"Updated notification preferences for user {user_id}")
    
    return success_response(
        data=user.notification_preferences.to_dict(),
        message='Notification preferences updated successfully'
    )


@preferences_bp.route('/email', methods=['GET'])
@jwt_required()
def get_email_preferences():
    """Get email preferences."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return error_response('User not found', status=404)
    
    if not user.email_preferences:
        initialize_user_preferences(user_id)
        db.session.refresh(user)
    
    return success_response(
        data=user.email_preferences.to_dict() if user.email_preferences else None,
        message='Email preferences retrieved'
    )


@preferences_bp.route('/email', methods=['PUT'])
@jwt_required()
def update_email_preferences():
    """Update email preferences with critical email protection."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return error_response('User not found', status=404)
    
    try:
        schema = EmailPreferencesSchema()
        data = schema.load(request.get_json())
    except ValidationError as err:
        return validation_error_response(err.messages)
    
    if not user.email_preferences:
        initialize_user_preferences(user_id)
        db.session.refresh(user)
    
    # Update preferences
    for key, value in data.items():
        if hasattr(user.email_preferences, key):
            setattr(user.email_preferences, key, value)
    
    db.session.commit()
    
    logger.info(f"Updated email preferences for user {user_id}")
    
    return success_response(
        data=user.email_preferences.to_dict(),
        message='Email preferences updated successfully'
    )


@preferences_bp.route('/privacy', methods=['GET'])
@jwt_required()
def get_privacy_settings():
    """Get privacy settings."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return error_response('User not found', status=404)
    
    if not user.privacy_settings:
        initialize_user_preferences(user_id)
        db.session.refresh(user)
    
    return success_response(
        data=user.privacy_settings.to_dict() if user.privacy_settings else None,
        message='Privacy settings retrieved'
    )


@preferences_bp.route('/privacy', methods=['PUT'])
@jwt_required()
def update_privacy_settings():
    """Update privacy settings."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return error_response('User not found', status=404)
    
    try:
        schema = PrivacySettingsSchema()
        data = schema.load(request.get_json())
    except ValidationError as err:
        return validation_error_response(err.messages)
    
    if not user.privacy_settings:
        initialize_user_preferences(user_id)
        db.session.refresh(user)
    
    for key, value in data.items():
        if hasattr(user.privacy_settings, key):
            setattr(user.privacy_settings, key, value)
    
    db.session.commit()
    
    logger.info(f"Updated privacy settings for user {user_id}")
    
    return success_response(
        data=user.privacy_settings.to_dict(),
        message='Privacy settings updated successfully'
    )


@preferences_bp.route('/localization', methods=['GET'])
@jwt_required()
def get_localization_settings():
    """Get localization settings."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return error_response('User not found', status=404)
    
    if not user.localization_settings:
        initialize_user_preferences(user_id)
        db.session.refresh(user)
    
    return success_response(
        data=user.localization_settings.to_dict() if user.localization_settings else None,
        message='Localization settings retrieved'
    )


@preferences_bp.route('/localization', methods=['PUT'])
@jwt_required()
def update_localization_settings():
    """Update localization settings and sync to User model."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return error_response('User not found', status=404)
    
    try:
        schema = LocalizationSettingsSchema()
        data = schema.load(request.get_json())
    except ValidationError as err:
        return validation_error_response(err.messages)
    
    if not user.localization_settings:
        initialize_user_preferences(user_id)
        db.session.refresh(user)
    
    for key, value in data.items():
        if hasattr(user.localization_settings, key):
            setattr(user.localization_settings, key, value)
    
    # Sync language and timezone to User model (cached fields)
    if 'language' in data:
        user.language = data['language']
    if 'timezone' in data:
        user.timezone = data['timezone']
    
    db.session.commit()
    
    logger.info(f"Updated localization settings for user {user_id}")
    
    return success_response(
        data=user.localization_settings.to_dict(),
        message='Localization settings updated successfully'
    )


@preferences_bp.route('/accessibility', methods=['GET'])
@jwt_required()
def get_accessibility_preferences():
    """Get accessibility preferences."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return error_response('User not found', status=404)
    
    if not user.accessibility_preferences:
        initialize_user_preferences(user_id)
        db.session.refresh(user)
    
    return success_response(
        data=user.accessibility_preferences.to_dict() if user.accessibility_preferences else None,
        message='Accessibility preferences retrieved'
    )


@preferences_bp.route('/accessibility', methods=['PUT'])
@jwt_required()
def update_accessibility_preferences():
    """Update accessibility preferences."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return error_response('User not found', status=404)
    
    try:
        schema = AccessibilityPreferencesSchema()
        data = schema.load(request.get_json())
    except ValidationError as err:
        return validation_error_response(err.messages)
    
    if not user.accessibility_preferences:
        initialize_user_preferences(user_id)
        db.session.refresh(user)
    
    for key, value in data.items():
        if hasattr(user.accessibility_preferences, key):
            setattr(user.accessibility_preferences, key, value)
    
    db.session.commit()
    
    logger.info(f"Updated accessibility preferences for user {user_id}")
    
    return success_response(
        data=user.accessibility_preferences.to_dict(),
        message='Accessibility preferences updated successfully'
    )


@preferences_bp.route('/billing', methods=['GET'])
@jwt_required()
def get_billing_preferences():
    """Get billing preferences."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return error_response('User not found', status=404)
    
    if not user.billing_preferences:
        initialize_user_preferences(user_id)
        db.session.refresh(user)
    
    return success_response(
        data=user.billing_preferences.to_dict() if user.billing_preferences else None,
        message='Billing preferences retrieved'
    )


@preferences_bp.route('/billing', methods=['PUT'])
@jwt_required()
def update_billing_preferences():
    """Update billing preferences."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return error_response('User not found', status=404)
    
    try:
        schema = BillingPreferencesSchema()
        data = schema.load(request.get_json())
    except ValidationError as err:
        return validation_error_response(err.messages)
    
    if not user.billing_preferences:
        initialize_user_preferences(user_id)
        db.session.refresh(user)
    
    for key, value in data.items():
        if hasattr(user.billing_preferences, key):
            setattr(user.billing_preferences, key, value)
    
    db.session.commit()
    
    logger.info(f"Updated billing preferences for user {user_id}")
    
    return success_response(
        data=user.billing_preferences.to_dict(),
        message='Billing preferences updated successfully'
    )


@preferences_bp.route('/export', methods=['GET'])
@jwt_required()
def export_preferences():
    """
    Export all user preferences (GDPR compliance).
    
    Returns complete preference data in portable format.
    """
    user_id = get_jwt_identity()
    
    export_data = export_user_preferences(user_id)
    
    if export_data is None:
        return error_response('User not found', status=404)
    
    return success_response(
        data=export_data,
        message='Preferences exported successfully'
    )


@preferences_bp.route('/import', methods=['POST'])
@jwt_required()
def import_preferences():
    """
    Import user preferences from export data (GDPR compliance).
    
    Validates and safely imports preference data.
    """
    user_id = get_jwt_identity()
    
    import_data = request.get_json()
    
    if not import_data:
        return error_response('No data provided', status=400)
    
    result = import_user_preferences(user_id, import_data)
    
    if not result.get('success'):
        return error_response(result.get('error', 'Import failed'), status=400)
    
    response_data = {
        'imported_categories': result.get('imported_categories', []),
        'validation_errors': result.get('validation_errors', [])
    }
    
    return success_response(
        data=response_data,
        message='Preferences imported successfully'
    )


@preferences_bp.route('/reset', methods=['POST'])
@jwt_required()
def reset_preferences():
    """
    Reset preferences to defaults.
    
    Query params:
        category (optional): Specific category to reset (notification, email, etc.)
    """
    user_id = get_jwt_identity()
    category = request.args.get('category')
    
    result = reset_preferences_to_defaults(user_id, category)
    
    if not result.get('success'):
        return error_response(result.get('error', 'Reset failed'), status=400)
    
    return success_response(
        data={'reset_categories': result.get('reset_categories', [])},
        message='Preferences reset to defaults successfully'
    )
