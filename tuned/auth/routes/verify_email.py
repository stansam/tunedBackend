"""
Email verification routes.

Handles email verification and resending verification emails.
"""
from flask import request
from marshmallow import ValidationError
from tuned.auth import auth_bp
from tuned.auth.schemas import EmailVerificationSchema, ResendVerificationSchema
from tuned.models.user import User
from tuned.extensions import db
from tuned.utils import success_response, error_response, validation_error_response
from tuned.utils import verify_verification_token, generate_verification_token
from tuned.utils.decorators import rate_limit
from tuned.services.email_service import send_verification_email, send_welcome_email_delayed
from tuned.services.notification_service import create_email_verified_notification
from tuned.models.audit import ActivityLog
from tuned.utils.auth import get_user_ip
from datetime import datetime, timezone
import logging


logger = logging.getLogger(__name__)


@auth_bp.route('/verify-email', methods=['POST'])
def verify_email():
    """
    Verify user email address with token.
    
    Request Body:
        {
            "token": "string"
        }
    
    Returns:
        200: Email verified successfully
        400: Invalid or expired token
        422: Validation error
    """
    try:
        # Get request data
        data = request.get_json()
        
        # Validate input
        schema = EmailVerificationSchema()
        validated_data = schema.load(data)
        
    except ValidationError as err:
        return validation_error_response(err.messages)
    except Exception as e:
        logger.error(f"Email verification validation error: {str(e)}")
        return error_response("Invalid request data", status=400)
    
    try:
        # Verify token
        token_data = verify_verification_token(validated_data['token'])
        
        if not token_data:
            logger.warning("Email verification attempted with invalid/expired token")
            return error_response(
                "Invalid or expired verification link. Please request a new verification email.",
                status=400
            )
        
        # Get user
        user = User.query.get(token_data['user_id'])
        
        if not user:
            logger.error(f"User not found for verification token: {token_data['user_id']}")
            return error_response("User not found", status=404)
        
        # Check if email matches (security check)
        if user.email != token_data['email']:
            logger.warning(f"Email mismatch during verification for user {user.id}")
            return error_response("Invalid verification link", status=400)
        
        # Check if already verified
        if user.email_verified:
            logger.info(f"Email already verified for user {user.id}")
            return success_response(message="Email already verified")
        
        # Mark email as verified
        user.email_verified = True
        db.session.commit()
        
        logger.info(f"Email verified successfully for user {user.id}")
        
        # Create notification
        create_email_verified_notification(user)
        
        # Send welcome email (delayed 15-30 mins)
        send_welcome_email_delayed(user)
        
        # Log activity
        ActivityLog.log(
            action='email_verified',
            user_id=user.id,
            entity_type='User',
            entity_id=user.id,
            description=f'Email verified: {user.email}',
            ip_address=get_user_ip(),
            user_agent=request.headers.get('User-Agent')
        )
        
        return success_response(
            message='Email verified successfully! You can now log in to your account.'
        )
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Email verification error: {str(e)}", exc_info=True)
        return error_response("An error occurred during email verification", status=500)


@auth_bp.route('/resend-verification', methods=['POST'])
@rate_limit(max_requests=3, window=300)  # 3 requests per 5 minutes
def resend_verification():
    """
    Resend email verification link.
    
    Request Body:
        {
            "email": "string"
        }
    
    Returns:
        200: Verification email sent
        400: Email already verified or user not found (generic message for security)
        422: Validation error
    """
    try:
        # Get request data
        data = request.get_json()
        
        # Validate input
        schema = ResendVerificationSchema()
        validated_data = schema.load(data)
        
    except ValidationError as err:
        return validation_error_response(err.messages)
    except Exception as e:
        logger.error(f"Resend verification validation error: {str(e)}")
        return error_response("Invalid request data", status=400)
    
    try:
        # Get user
        user = User.query.filter_by(email=validated_data['email'].lower()).first()
        
        # Generic response for security (don't reveal if email exists)
        success_msg = "If an account with that email exists and is not verified, a new verification email has been sent."
        
        if not user:
            logger.info(f"Resend verification requested for non-existent email: {validated_data['email']}")
            return success_response(message=success_msg)
        
        # Check if already verified
        if user.email_verified:
            logger.info(f"Resend verification requested for already verified user {user.id}")
            return success_response(message=success_msg)
        
        # Generate new verification token
        verification_token = generate_verification_token(user.id, user.email)
        
        # Send verification email
        send_verification_email(user, verification_token)
        
        logger.info(f"Verification email resent to user {user.id}")
        
        # Log activity
        ActivityLog.log(
            action='verification_email_resent',
            user_id=user.id,
            entity_type='User',
            entity_id=user.id,
            description=f'Verification email resent to: {user.email}',
            ip_address=get_user_ip(),
            user_agent=request.headers.get('User-Agent')
        )
        
        return success_response(message=success_msg)
        
    except Exception as e:
        logger.error(f"Resend verification error: {str(e)}", exc_info=True)
        return error_response("An error occurred. Please try again.", status=500)
