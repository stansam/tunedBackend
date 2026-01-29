"""
Password reset routes.

Handles password reset request and confirmation.
"""
from flask import request
from marshmallow import ValidationError
from tuned.auth import auth_bp
from tuned.auth.schemas import PasswordResetRequestSchema, PasswordResetConfirmSchema
from tuned.models.user import User
from tuned.extensions import db
from tuned.utils import success_response, error_response, validation_error_response
from tuned.utils import generate_password_reset_token, verify_password_reset_token
from tuned.utils.auth import hash_password, get_user_ip
from tuned.utils.decorators import rate_limit
from tuned.services.email_service import send_password_reset_email, send_password_changed_email
from tuned.services.notification_service import create_password_changed_notification
from tuned.models.audit import ActivityLog
from datetime import datetime, timezone
import logging


logger = logging.getLogger(__name__)


@auth_bp.route('/password-reset/request', methods=['POST'])
@rate_limit(max_requests=3, window=300)  # 3 requests per 5 minutes
def password_reset_request():
    """
    Request a password reset link.
    
    Request Body:
        {
            "email": "string"
        }
    
    Returns:
        200: Always returns success (security - don't reveal if email exists)
    """
    try:
        # Get request data
        data = request.get_json()
        
        # Validate input
        schema = PasswordResetRequestSchema()
        validated_data = schema.load(data)
        
    except ValidationError as err:
        return validation_error_response(err.messages)
    except Exception as e:
        logger.error(f"Password reset request validation error: {str(e)}")
        return error_response("Invalid request data", status=400)
    
    try:
        # Generic success message (don't reveal if email exists)
        success_msg = "If an account with that email exists, a password reset link has been sent."
        
        # Get user
        user = User.query.filter_by(email=validated_data['email'].lower()).first()
        
        if not user:
            logger.info(f"Password reset requested for non-existent email: {validated_data['email']}")
            # Still return success for security
            return success_response(message=success_msg)
        
        # Check if account is active
        if not user.is_active or user.deleted_at:
            logger.warning(f"Password reset requested for deactivated account: {user.id}")
            return success_response(message=success_msg)
        
        # Generate reset token
        reset_token = generate_password_reset_token(user.id, user.email)
        
        # Send password reset email
        send_password_reset_email(user, reset_token)
        
        logger.info(f"Password reset email sent to user {user.id}")
        
        # Log activity
        ActivityLog.log(
            action='password_reset_requested',
            user_id=user.id,
            entity_type='User',
            entity_id=user.id,
            description=f'Password reset requested from IP {get_user_ip()}',
            ip_address=get_user_ip(),
            user_agent=request.headers.get('User-Agent')
        )
        
        return success_response(message=success_msg)
        
    except Exception as e:
        logger.error(f"Password reset request error: {str(e)}", exc_info=True)
        return error_response("An error occurred. Please try again.", status=500)


@auth_bp.route('/password-reset/confirm', methods=['POST'])
@rate_limit(max_requests=5, window=300)  # 5 attempts per 5 minutes
def password_reset_confirm():
    """
    Confirm password reset with token and new password.
    
    Request Body:
        {
            "token": "string",
            "new_password": "string",
            "confirm_password": "string"
        }
    
    Returns:
        200: Password reset successful
        400: Invalid or expired token
        422: Validation error
    """
    try:
        # Get request data
        data = request.get_json()
        
        # Validate input
        schema = PasswordResetConfirmSchema()
        validated_data = schema.load(data)
        
    except ValidationError as err:
        return validation_error_response(err.messages)
    except Exception as e:
        logger.error(f"Password reset confirm validation error: {str(e)}")
        return error_response("Invalid request data", status=400)
    
    try:
        # Verify token
        token_data = verify_password_reset_token(validated_data['token'])
        
        if not token_data:
            logger.warning("Password reset attempted with invalid/expired token")
            return error_response(
                "Invalid or expired reset link. Please request a new password reset.",
                status=400
            )
        
        # Get user
        user = User.query.get(token_data['user_id'])
        
        if not user:
            logger.error(f"User not found for password reset token: {token_data['user_id']}")
            return error_response("User not found", status=404)
        
        # Check if email matches (security check)
        if user.email != token_data['email']:
            logger.warning(f"Email mismatch during password reset for user {user.id}")
            return error_response("Invalid reset link", status=400)
        
        # Check if account is active
        if not user.is_active or user.deleted_at:
            logger.warning(f"Password reset attempted for deactivated account: {user.id}")
            return error_response("This account has been deactivated", status=403)
        
        # Update password
        user.password_hash = hash_password(validated_data['new_password'])
        
        # Reset failed login attempts
        user.failed_login_attempts = 0
        user.last_failed_login = None
        
        db.session.commit()
        
        logger.info(f"Password reset successful for user {user.id}")
        
        # Create notification
        create_password_changed_notification(user)
        
        # Send confirmation email
        send_password_changed_email(user)
        
        # Log activity
        ActivityLog.log(
            action='password_reset_completed',
            user_id=user.id,
            entity_type='User',
            entity_id=user.id,
            description=f'Password reset from IP {get_user_ip()}',
            ip_address=get_user_ip(),
            user_agent=request.headers.get('User-Agent')
        )
        
        return success_response(
            message='Password reset successful! You can now log in with your new password.'
        )
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Password reset confirm error: {str(e)}", exc_info=True)
        return error_response("An error occurred during password reset", status=500)
