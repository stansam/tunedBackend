"""
Profile management routes for client blueprint.

Handles profile information updates, picture management, and account settings.
"""

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


@client_bp.route('/profile/picture', methods=['POST'])
@jwt_required()
@rate_limit(max_requests=10, window=3600)
@log_activity('profile_picture_updated', 'User')
def update_profile_picture():
    """
    Upload/update profile picture.
    
    Form Data:
        file: Image file (jpg, jpeg, png, gif, webp)
        crop_data: Optional JSON with crop coordinates
    
    Returns:
        200: Profile picture updated successfully
        400: Invalid file or file type
    """
    current_user_id = get_jwt_identity()
    
    try:
        if 'file' not in request.files:
            return error_response('No file provided', status=400)
        
        file = request.files['file']
        
        if file.filename == '':
            return error_response('No file selected', status=400)
        
        # Validate file type
        allowed_extensions = {'jpg', 'jpeg', 'png', 'gif', 'webp'}
        if not ('.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
            return error_response(
                f'Invalid file type. Allowed: {", ".join(allowed_extensions)}',
                status=400
            )
        
        # Check file size (5MB max)
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        max_size = 5 * 1024 * 1024  # 5MB
        if file_size > max_size:
            return error_response('File size exceeds 5MB limit', status=400)
        
        user = User.query.get(current_user_id)
        
        if not user:
            return error_response('User not found', status=404)
        
        # Generate secure filename
        filename = secure_filename(file.filename)
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        new_filename = f"profile_{user.id}_{timestamp}_{filename}"
        
        # Save file (In production, upload to S3 or similar)
        upload_folder = os.path.join('uploads', 'profiles')
        os.makedirs(upload_folder, exist_ok=True)
        
        file_path = os.path.join(upload_folder, new_filename)
        file.save(file_path)
        
        # Update user profile picture URL
        # In production, this would be the S3 URL
        user.profile_picture = f'/uploads/profiles/{new_filename}'
        user.updated_at = datetime.now(timezone.utc)
        
        db.session.commit()
        
        logger.info(f'Profile picture updated for user {current_user_id}')
        
        return success_response(
            data={'profile_picture': user.profile_picture},
            message='Profile picture updated successfully'
        )
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error updating profile picture for user {current_user_id}: {str(e)}', exc_info=True)
        return error_response('An error occurred while updating your profile picture', status=500)


@client_bp.route('/profile/picture', methods=['DELETE'])
@jwt_required()
@rate_limit(max_requests=10, window=3600)
@log_activity('profile_picture_deleted', 'User')
def delete_profile_picture():
    """
    Delete profile picture.
    
    Request Body:
        {
            "confirm": bool (must be true)
        }
    
    Returns:
        200: Profile picture deleted successfully
        400: Confirmation required
    """
    current_user_id = get_jwt_identity()
    
    # Validate confirmation
    schema = DeleteProfilePictureSchema()
    try:
        data = schema.load(request.get_json())
    except ValidationError as e:
        return validation_error_response(e.messages)
    
    try:
        user = User.query.get(current_user_id)
        
        if not user:
            return error_response('User not found', status=404)
        
        if not user.profile_picture:
            return error_response('No profile picture to delete', status=400)
        
        # Delete file if it exists locally
        # In production, delete from S3
        
        user.profile_picture = None
        user.updated_at = datetime.now(timezone.utc)
        
        db.session.commit()
        
        logger.info(f'Profile picture deleted for user {current_user_id}')
        
        return success_response(
            message='Profile picture deleted successfully'
        )
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error deleting profile picture for user {current_user_id}: {str(e)}', exc_info=True)
        return error_response('An error occurred while deleting your profile picture', status=500)
