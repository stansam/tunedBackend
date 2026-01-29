"""
User registration route.

Handles new user registration with email verification requirement.
"""
from flask import request
from flask_jwt_extended import create_access_token, create_refresh_token, set_access_cookies, set_refresh_cookies
from marshmallow import ValidationError
from tuned.auth import auth_bp
from tuned.auth.schemas import RegistrationSchema
from tuned.models.user import User, GenderEnum
from tuned.extensions import db
from tuned.utils import success_response, error_response, validation_error_response, created_response
from tuned.utils import generate_verification_token, generate_referral_code
from tuned.utils.auth import hash_password, get_user_ip
from tuned.utils.decorators import rate_limit
from tuned.services.email_service import send_verification_email
from tuned.services.notification_service import create_welcome_notification
from tuned.models.audit import ActivityLog
from datetime import datetime, timezone
import logging


logger = logging.getLogger(__name__)


@auth_bp.route('/register', methods=['POST'])
@rate_limit(max_requests=3, window=300)  # 3 attempts per 5 minutes
def register():
    """
    Register a new user account.
    
    Request Body:
        {
            "username": "string",
            "email": "string",
            "password": "string",
            "confirm_password": "string",
            "first_name": "string",
            "last_name": "string",
            "gender": "male | female",
            "phone_number": "string (optional)"
        }
    
    Returns:
        201: User created successfully, verification email sent
        400: Validation error
        422: Invalid data format
    """
    try:
        # Get request data
        data = request.get_json()
        
        # Validate input with schema
        schema = RegistrationSchema()
        validated_data = schema.load(data)
        
    except ValidationError as err:
        return validation_error_response(err.messages)
    except Exception as e:
        logger.error(f"Registration validation error: {str(e)}")
        return error_response("Invalid request data", status=400)
    
    try:
        # Create new user
        user = User(
            username=validated_data['username'],
            email=validated_data['email'].lower(),
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            gender=GenderEnum[validated_data['gender'].lower()],
            phone_number=validated_data.get('phone_number'),
            email_verified=False,  # Require email verification
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        
        # Set password (hashed)
        user.password_hash = hash_password(validated_data['password'])
        
        # Generate referral code
        user.referral_code = generate_referral_code()
        
        # Save to database
        db.session.add(user)
        db.session.commit()
        
        logger.info(f"New user registered: {user.id} ({user.email})")
        
        # Generate verification token
        verification_token = generate_verification_token(user.id, user.email)
        
        # Send verification email asynchronously
        send_verification_email(user, verification_token)
        
        # Create welcome notification
        create_welcome_notification(user)
        
        # Log activity
        ActivityLog.log(
            action='user_registered',
            user_id=user.id,
            entity_type='User',
            entity_id=user.id,
            description=f'New user registered: {user.email}',
            ip_address=get_user_ip(),
            user_agent=request.headers.get('User-Agent')
        )
        
        # Prepare response data (exclude sensitive fields)
        user_data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email_verified': user.email_verified,
            'referral_code': user.referral_code
        }
        
        return created_response(
            data=user_data,
            message='Registration successful! Please check your email to verify your account.'
        )
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Registration error: {str(e)}", exc_info=True)
        return error_response("An error occurred during registration. Please try again.", status=500)
