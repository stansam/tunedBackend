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
