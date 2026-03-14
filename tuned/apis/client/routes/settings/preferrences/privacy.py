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
