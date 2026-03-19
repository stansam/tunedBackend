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

@client_bp.route('/profile', methods=['PUT'])
@jwt_required()
@rate_limit(max_requests=20, window=3600)
@log_activity('profile_updated', 'User')
def update_profile():
    """
    Update current user's profile information.
    
    Request Body:
        {
            "first_name": str (optional, 1-50 chars),
            "last_name": str (optional, 1-50 chars),
            "phone": str (optional, international format),
            "gender": str (optional, male/female/other/prefer_not_to_say),
            "date_of_birth": str (optional, YYYY-MM-DD, min age 13),
            "bio": str (optional, max 500 chars),
            "country": str (optional, max 100 chars),
            "city": str (optional, max 100 chars),
            "timezone": str (optional, max 50 chars)
        }
    
    Returns:
        200: Profile updated successfully
        400: Validation error
    """
    current_user_id = get_jwt_identity()
    
    # Validate input
    schema = UpdateProfileSchema()
    try:
        data = schema.load(request.get_json())
    except ValidationError as e:
        return validation_error_response(e.messages)
    
    try:
        user = User.query.get(current_user_id)
        
        if not user:
            return error_response('User not found', status=404)
        
        # Update fields
        if 'first_name' in data:
            user.first_name = data['first_name']
        
        if 'last_name' in data:
            user.last_name = data['last_name']
        
        if 'phone' in data:
            user.phone = data['phone']
        
        if 'gender' in data:
            user.gender = data['gender']
        
        if 'date_of_birth' in data:
            user.date_of_birth = data['date_of_birth']
        
        if 'bio' in data:
            user.bio = data['bio']
        
        if 'country' in data:
            user.country = data['country']
        
        if 'city' in data:
            user.city = data['city']
        
        if 'timezone' in data:
            user.timezone = data['timezone']
        
        user.updated_at = datetime.now(timezone.utc)
        
        db.session.commit()
        
        logger.info(f'Profile updated for user {current_user_id}')
        
        # Return updated profile
        profile_data = {
            'id': user.id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'full_name': user.get_name(),
            'phone': user.phone,
            'gender': user.gender.value if user.gender else None,
            'date_of_birth': user.date_of_birth.isoformat() if user.date_of_birth else None,
            'bio': user.bio,
            'country': user.country,
            'city': user.city,
            'timezone': user.timezone,
            'updated_at': user.updated_at.isoformat()
        }
        
        return success_response(
            data={'profile': profile_data},
            message='Profile updated successfully'
        )
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error updating profile for user {current_user_id}: {str(e)}', exc_info=True)
        return error_response('An error occurred while updating your profile', status=500)


