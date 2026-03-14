from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError
from datetime import datetime, timezone
from werkzeug.utils import secure_filename
import os
import logging

from tuned.client import client_bp
from tuned.client.schemas import (
    UpdateProfileSchema,
    UpdateProfilePictureSchema,
    DeleteProfilePictureSchema
)
from tuned.models.user import User
from tuned.extensions import db
from tuned.utils import success_response, error_response, validation_error_response
from tuned.utils.decorators import rate_limit, log_activity

logger = logging.getLogger(__name__)

@client_bp.route('/profile', methods=['GET'])
@jwt_required()
@rate_limit(max_requests=100, window=60)
def get_profile():
    """
    Get current user's profile information.
    
    Returns:
        200: Profile data
        404: User not found
    """
    current_user_id = get_jwt_identity()
    
    try:
        user = User.query.get(current_user_id)
        
        if not user:
            return error_response('User not found', status=404)
        
        # Serialize profile data
        profile_data = {
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'full_name': user.get_name(),
            'phone': user.phone,
            'gender': user.gender.value if user.gender else None,
            'date_of_birth': user.date_of_birth.isoformat() if user.date_of_birth else None,
            'bio': user.bio,
            'profile_picture': user.profile_picture,
            'country': user.country,
            'city': user.city,
            'timezone': user.timezone,
            'language': user.language or 'en',
            'email_verified': user.email_verified,
            'created_at': user.created_at.isoformat()
        }
        
        logger.info(f'Profile retrieved for user {current_user_id}')
        
        return success_response(
            data={'profile': profile_data},
            message='Profile retrieved successfully'
        )
        
    except Exception as e:
        logger.error(f'Error retrieving profile for user {current_user_id}: {str(e)}', exc_info=True)
        return error_response('An error occurred while retrieving your profile', status=500)
