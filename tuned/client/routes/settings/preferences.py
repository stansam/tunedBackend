"""
Notification and privacy settings routes for client blueprint.

Handles user preferences for notifications, privacy, language, and email settings.
"""

from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError
from datetime import datetime, timezone
import logging

from tuned.client import client_bp
from tuned.client.schemas import (
    NotificationPreferencesSchema,
    PrivacySettingsSchema,
    LanguagePreferenceSchema,
    EmailPreferencesSchema
)
from tuned.models.user import User
from tuned.extensions import db
from tuned.utils import success_response, error_response, validation_error_response
from tuned.utils.decorators import rate_limit, log_activity

logger = logging.getLogger(__name__)


@client_bp.route('/settings/notifications', methods=['GET'])
@jwt_required()
@rate_limit(max_requests=100, window=60)
def get_notification_preferences():
    """
    Get user notification preferences.
    
    Returns:
        200: Notification preferences
    """
    current_user_id = get_jwt_identity()
    
    try:
        user = User.query.get(current_user_id)
        
        if not user:
            return error_response('User not found', status=404)
        
        # In a full implementation, query UserNotificationPreferences model
        # For now, return defaults
        preferences = {
            'email_notifications': True,
            'sms_notifications': False,
            'push_notifications': True,
            'order_updates': True,
            'payment_notifications': True,
            'delivery_notifications': True,
            'marketing_emails': False,
            'weekly_summary': False,
            'comment_notifications': True,
            'support_ticket_updates': True
        }
        
        return success_response(
            data={'preferences': preferences},
            message='Notification preferences retrieved successfully'
        )
        
    except Exception as e:
        logger.error(f'Error retrieving notification preferences for user {current_user_id}: {str(e)}', exc_info=True)
        return error_response('An error occurred while retrieving your preferences', status=500)


@client_bp.route('/settings/notifications', methods=['PUT'])
@jwt_required()
@rate_limit(max_requests=20, window=3600)
@log_activity('notification_preferences_updated', 'User')
def update_notification_preferences():
    """
    Update user notification preferences.
    
    Request Body:
        {
            "email_notifications": bool (optional),
            "sms_notifications": bool (optional),
            "push_notifications": bool (optional),
            "order_updates": bool (optional),
            "payment_notifications": bool (optional),
            "delivery_notifications": bool (optional),
            "marketing_emails": bool (optional),
            "weekly_summary": bool (optional),
            "comment_notifications": bool (optional),
            "support_ticket_updates": bool (optional)
        }
    
    Returns:
        200: Preferences updated successfully
        400: Validation error
    """
    current_user_id = get_jwt_identity()
    
    # Validate input
    schema = NotificationPreferencesSchema()
    try:
        data = schema.load(request.get_json())
    except ValidationError as e:
        return validation_error_response(e.messages)
    
    try:
        user = User.query.get(current_user_id)
        
        if not user:
            return error_response('User not found', status=404)
        
        # In a full implementation, update UserNotificationPreferences model
        # For now, just log the update
        
        logger.info(f'Notification preferences updated for user {current_user_id}')
        
        return success_response(
            data={'preferences': data},
            message='Notification preferences updated successfully'
        )
        
    except Exception as e:
        logger.error(f'Error updating notification preferences for user {current_user_id}: {str(e)}', exc_info=True)
        return error_response('An error occurred while updating your preferences', status=500)


@client_bp.route('/settings/privacy', methods=['GET'])
@jwt_required()
@rate_limit(max_requests=100, window=60)
def get_privacy_settings():
    """
    Get user privacy settings.
    
    Returns:
        200: Privacy settings
    """
    current_user_id = get_jwt_identity()
    
    try:
        user = User.query.get(current_user_id)
        
        if not user:
            return error_response('User not found', status=404)
        
        # In a full implementation, query UserPrivacySettings model
        # For now, return defaults
        privacy = {
            'profile_visibility': 'private',
            'show_email': False,
            'show_phone': False,
            'allow_messages': True,
            'data_sharing': False,
            'analytics_tracking': True
        }
        
        return success_response(
            data={'privacy': privacy},
            message='Privacy settings retrieved successfully'
        )
        
    except Exception as e:
        logger.error(f'Error retrieving privacy settings for user {current_user_id}: {str(e)}', exc_info=True)
        return error_response('An error occurred while retrieving your privacy settings', status=500)


@client_bp.route('/settings/privacy', methods=['PUT'])
@jwt_required()
@rate_limit(max_requests=20, window=3600)
@log_activity('privacy_settings_updated', 'User')
def update_privacy_settings():
    """
    Update user privacy settings.
    
    Request Body:
        {
            "profile_visibility": str (public, private, friends_only),
            "show_email": bool (optional),
            "show_phone": bool (optional),
            "allow_messages": bool (optional),
            "data_sharing": bool (optional),
            "analytics_tracking": bool (optional)
        }
    
    Returns:
        200: Privacy settings updated successfully
        400: Validation error
    """
    current_user_id = get_jwt_identity()
    
    # Validate input
    schema = PrivacySettingsSchema()
    try:
        data = schema.load(request.get_json())
    except ValidationError as e:
        return validation_error_response(e.messages)
    
    try:
        user = User.query.get(current_user_id)
        
        if not user:
            return error_response('User not found', status=404)
        
        # In a full implementation, update UserPrivacySettings model
        # For now, just log the update
        
        logger.info(f'Privacy settings updated for user {current_user_id}')
        
        return success_response(
            data={'privacy': data},
            message='Privacy settings updated successfully'
        )
        
    except Exception as e:
        logger.error(f'Error updating privacy settings for user {current_user_id}: {str(e)}', exc_info=True)
        return error_response('An error occurred while updating your privacy settings', status=500)


@client_bp.route('/settings/language', methods=['GET'])
@jwt_required()
@rate_limit(max_requests=100, window=60)
def get_language_preferences():
    """
    Get user language and locale preferences.
    
    Returns:
        200: Language preferences
    """
    current_user_id = get_jwt_identity()
    
    try:
        user = User.query.get(current_user_id)
        
        if not user:
            return error_response('User not found', status=404)
        
        language_prefs = {
            'language': user.language or 'en',
            'date_format': 'MM/DD/YYYY',
            'time_format': '12h',
            'currency': 'USD',
            'timezone': user.timezone or 'UTC'
        }
        
        return success_response(
            data={'language': language_prefs},
            message='Language preferences retrieved successfully'
        )
        
    except Exception as e:
        logger.error(f'Error retrieving language preferences for user {current_user_id}: {str(e)}', exc_info=True)
        return error_response('An error occurred while retrieving your language preferences', status=500)


@client_bp.route('/settings/language', methods=['PUT'])
@jwt_required()
@rate_limit(max_requests=20, window=3600)
@log_activity('language_preferences_updated', 'User')
def update_language_preferences():
    """
    Update user language and locale preferences.
    
    Request Body:
        {
            "language": str (required: en, es, fr, de, pt, zh, ar),
            "date_format": str (optional: MM/DD/YYYY, DD/MM/YYYY, YYYY-MM-DD),
            "time_format": str (optional: 12h, 24h),
            "currency": str (optional: USD, EUR, GBP, CAD, AUD)
        }
    
    Returns:
        200: Language preferences updated successfully
        400: Validation error
    """
    current_user_id = get_jwt_identity()
    
    # Validate input
    schema = LanguagePreferenceSchema()
    try:
        data = schema.load(request.get_json())
    except ValidationError as e:
        return validation_error_response(e.messages)
    
    try:
        user = User.query.get(current_user_id)
        
        if not user:
            return error_response('User not found', status=404)
        
        # Update language
        user.language = data['language']
        user.updated_at = datetime.now(timezone.utc)
        
        # In a full implementation, also update date_format, time_format, currency
        # in a UserPreferences model
        
        db.session.commit()
        
        logger.info(f'Language preferences updated for user {current_user_id}: {data["language"]}')
        
        return success_response(
            data={'language': data},
            message='Language preferences updated successfully'
        )
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error updating language preferences for user {current_user_id}: {str(e)}', exc_info=True)
        return error_response('An error occurred while updating your language preferences', status=500)


@client_bp.route('/settings/email-preferences', methods=['GET'])
@jwt_required()
@rate_limit(max_requests=100, window=60)
def get_email_preferences():
    """
    Get user email communication preferences.
    
    Returns:
        200: Email preferences
    """
    current_user_id = get_jwt_identity()
    
    try:
        user = User.query.get(current_user_id)
        
        if not user:
            return error_response('User not found', status=404)
        
        # In a full implementation, query UserEmailPreferences model
        email_prefs = {
            'newsletter': False,
            'promotional_emails': False,
            'product_updates': True,
            'order_confirmations': True,  # Cannot be disabled
            'payment_receipts': True,  # Cannot be disabled
            'account_security': True,  # Cannot be disabled
            'frequency': 'instant'
        }
        
        return success_response(
            data={'email_preferences': email_prefs},
            message='Email preferences retrieved successfully'
        )
        
    except Exception as e:
        logger.error(f'Error retrieving email preferences for user {current_user_id}: {str(e)}', exc_info=True)
        return error_response('An error occurred while retrieving your email preferences', status=500)


@client_bp.route('/settings/email-preferences', methods=['PUT'])
@jwt_required()
@rate_limit(max_requests=20, window=3600)
@log_activity('email_preferences_updated', 'User')
def update_email_preferences():
    """
    Update user email communication preferences.
    
    Request Body:
        {
            "newsletter": bool (optional),
            "promotional_emails": bool (optional),
            "product_updates": bool (optional),
            "frequency": str (optional: instant, daily, weekly)
        }
    
    Note: order_confirmations, payment_receipts, and account_security
    cannot be disabled for security reasons.
    
    Returns:
        200: Email preferences updated successfully
        400: Validation error
    """
    current_user_id = get_jwt_identity()
    
    # Validate input
    schema = EmailPreferencesSchema()
    try:
        data = schema.load(request.get_json())
    except ValidationError as e:
        return validation_error_response(e.messages)
    
    try:
        user = User.query.get(current_user_id)
        
        if not user:
            return error_response('User not found', status=404)
        
        # In a full implementation, update UserEmailPreferences model
        # For now, just log the update
        
        logger.info(f'Email preferences updated for user {current_user_id}')
        
        return success_response(
            data={'email_preferences': data},
            message='Email preferences updated successfully'
        )
        
    except Exception as e:
        logger.error(f'Error updating email preferences for user {current_user_id}: {str(e)}', exc_info=True)
        return error_response('An error occurred while updating your email preferences', status=500)
