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

