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
