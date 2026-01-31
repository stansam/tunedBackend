"""
Password and email change routes for client blueprint.

Handles secure password updates and email address changes.
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


# Import existing schema
from tuned.client.schemas.settings.profile.change_password import ChangePasswordSchema


class ChangeEmailSchema(Schema):
    """Validation schema for email change request."""
    
    new_email = fields.Email(
        required=True,
        error_messages={'required': 'New email is required'}
    )
    
    password = fields.Str(
        required=True,
        validate=validate.Length(min=1),
        error_messages={'required': 'Password is required for verification'}
    )


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


@client_bp.route('/settings/email', methods=['PUT'])
@jwt_required()
@rate_limit(max_requests=3, window=86400)  # 3 email changes per day
@log_activity('email_change_requested', 'User')
def change_email():
    """
    Request email address change.
    
    Request Body:
        {
            "new_email": str (required, valid email),
            "password": str (required, for verification)
        }
    
    Returns:
        200: Email change confirmation sent
        400: Validation error, incorrect password, or email already in use
        429: Too many attempts
    """
    current_user_id = get_jwt_identity()
    
    # Validate input
    schema = ChangeEmailSchema()
    try:
        data = schema.load(request.get_json())
    except ValidationError as e:
        return validation_error_response(e.messages)
    
    try:
        user = User.query.get(current_user_id)
        
        if not user:
            return error_response('User not found', status=404)
        
        # Verify password
        if not check_password_hash(user.password_hash, data['password']):
            logger.warning(f'Failed email change attempt for user {current_user_id}: incorrect password')
            return error_response('Password is incorrect', status=400)
        
        new_email = data['new_email'].lower()
        
        # Check if new email is same as current
        if new_email == user.email:
            return error_response('New email is the same as current email', status=400)
        
        # Check if email is already in use
        existing_user = User.query.filter_by(email=new_email).first()
        if existing_user:
            return error_response('Email address is already in use', status=400)
        
        # In a full implementation, send confirmation email to new address
        # and only update after user confirms via token link
        # For now, we'll update directly
        
        old_email = user.email
        user.email = new_email
        user.email_verified = False  # Require re-verification
        user.updated_at = datetime.now(timezone.utc)
        
        db.session.commit()
        
        logger.info(f'Email changed for user {current_user_id}: {old_email} -> {new_email}')
        
        # Send notification
        try:
            create_notification(
                user_id=current_user_id,
                title='Email Address Changed',
                message=f'Your email has been changed to {new_email}. Please verify your new email address.',
                type=NotificationType.WARNING,
                link='/settings/account'
            )
        except Exception as e:
            logger.error(f'Notification error for email change: {str(e)}')
        
        # Send confirmation emails
        try:
            # Email to old address
            send_email_change_confirmation(old_email, new_email, user.get_name())
            # Email to new address with verification link
            # send_email_verification(user, new_email)
        except Exception as e:
            logger.error(f'Email error for email change: {str(e)}')
        
        return success_response(
            data={'new_email': new_email},
            message='Email address changed successfully. Please verify your new email address.'
        )
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error changing email for user {current_user_id}: {str(e)}', exc_info=True)
        return error_response('An error occurred while changing your email address', status=500)


@client_bp.route('/settings/security', methods=['GET'])
@jwt_required()
@rate_limit(max_requests=100, window=60)
def get_security_info():
    """
    Get user security information.
    
    Returns:
        200: Security settings and activity
    """
    current_user_id = get_jwt_identity()
    
    try:
        user = User.query.get(current_user_id)
        
        if not user:
            return error_response('User not found', status=404)
        
        security_data = {
            'email': user.email,
            'email_verified': user.email_verified,
            'password_changed_at': user.password_changed_at.isoformat() if user.password_changed_at else None,
            'last_login': user.last_login.isoformat() if user.last_login else None,
            'created_at': user.created_at.isoformat(),
            'two_factor_enabled': False,  # Placeholder for future 2FA feature
            'active_sessions': 1  # Placeholder
        }
        
        return success_response(
            data={'security': security_data},
            message='Security information retrieved successfully'
        )
        
    except Exception as e:
        logger.error(f'Error retrieving security info for user {current_user_id}: {str(e)}', exc_info=True)
        return error_response('An error occurred while retrieving security information', status=500)
