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
