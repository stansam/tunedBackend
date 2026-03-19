"""
Password change route for client blueprint.

Handles secure password update.
"""
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError, Schema, fields, validates, validate
from datetime import datetime, timezone
from werkzeug.security import check_password_hash, generate_password_hash
import logging

from tuned.client import client_bp
from tuned.models.user import User
from tuned.extensions import db
from tuned.utils import success_response, error_response, validation_error_response
from tuned.utils.decorators import rate_limit, log_activity
from tuned.services.notification_service import create_notification
from tuned.services.email_service import send_password_changed_email, send_email_change_confirmation
from tuned.models.enums import NotificationType

logger = logging.getLogger(__name__)

@client_bp.route('/settings/password', methods=['PUT'])
@jwt_required()
@rate_limit(max_requests=5, window=3600)  # 5 password changes per hour
@log_activity('password_changed', 'User')
def change_password():
    """
    Change user password.
    
    Request Body:
        {
            "current_password": str (required),
            "new_password": str (required, min 8 chars, must contain uppercase, lowercase, digit, special char),
            "confirm_password": str (required, must match new_password)
        }
    
    Returns:
        200: Password changed successfully
        400: Validation error or incorrect current password
        429: Too many attempts
    """
    current_user_id = get_jwt_identity()
    
    # Validate input
    schema = ChangePasswordSchema()
    try:
        data = schema.load(request.get_json())
    except ValidationError as e:
        return validation_error_response(e.messages)
    
    try:
        user = User.query.get(current_user_id)
        
        if not user:
            return error_response('User not found', status=404)
        
        # Verify current password
        if not check_password_hash(user.password_hash, data['current_password']):
            logger.warning(f'Failed password change attempt for user {current_user_id}: incorrect current password')
            return error_response('Current password is incorrect', status=400)
        
        # Update password
        user.password_hash = generate_password_hash(data['new_password'])
        user.password_changed_at = datetime.now(timezone.utc)
        user.updated_at = datetime.now(timezone.utc)
        
        db.session.commit()
        
        logger.info(f'Password changed for user {current_user_id}')
        
        # Send notification
        try:
            create_notification(
                user_id=current_user_id,
                title='Password Changed',
                message='Your password has been changed successfully. If you did not make this change, please contact support immediately.',
                type=NotificationType.WARNING,
                link='/settings/security'
            )
        except Exception as e:
            logger.error(f'Notification error for password change: {str(e)}')
        
        # Send security email
        try:
            send_password_changed_email(user)
        except Exception as e:
            logger.error(f'Email error for password change: {str(e)}')
        
        return success_response(
            message='Password changed successfully'
        )
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error changing password for user {current_user_id}: {str(e)}', exc_info=True)
        return error_response('An error occurred while changing your password', status=500)


