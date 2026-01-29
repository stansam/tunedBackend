"""
User login route.

Handles user authentication with JWT token generation.
Requires email verification before allowing login.
"""
from flask import request
from flask_jwt_extended import create_access_token, create_refresh_token, set_access_cookies, set_refresh_cookies
from marshmallow import ValidationError
from tuned.auth import auth_bp
from tuned.auth.schemas import LoginSchema
from tuned.extensions import db
from tuned.utils import success_response, error_response, validation_error_response, unauthorized_response
from tuned.utils.auth import verify_password, check_account_lockout, record_login_attempt, get_user_by_email_or_username, get_user_ip
from tuned.utils.decorators import rate_limit
from tuned.models.audit import ActivityLog
from datetime import timedelta
import logging


logger = logging.getLogger(__name__)


@auth_bp.route('/login', methods=['POST'])
@rate_limit(max_requests=5, window=60)  # 5 attempts per minute
def login():
    """
    Authenticate user and return JWT tokens.
    
    Request Body:
        {
            "email": "string",  # Can be email or username
            "password": "string",
            "remember_me": "boolean (optional)"
        }
    
    Returns:
        200: Authentication successful, returns tokens and user data
        401: Invalid credentials
        403: Account locked or email not verified
        422: Validation error
    """
    try:
        # Get request data
        data = request.get_json()
        
        # Validate input
        schema = LoginSchema()
        validated_data = schema.load(data)
        
    except ValidationError as err:
        return validation_error_response(err.messages)
    except Exception as e:
        logger.error(f"Login validation error: {str(e)}")
        return error_response("Invalid request data", status=400)
    
    try:
        # Get user by email or username
        user = get_user_by_email_or_username(validated_data['email'])
        
        if not user:
            # Don't reveal whether user exists
            logger.warning(f"Login attempt for non-existent user: {validated_data['email']}")
            return unauthorized_response("Invalid email or password")
        
        # Check account lockout
        is_locked, lock_message = check_account_lockout(user)
        if is_locked:
            logger.warning(f"Login attempt on locked account: {user.id}")
            return error_response(lock_message, status=403)
        
        # Verify password
        if not verify_password(validated_data['password'], user.password_hash):
            # Record failed attempt
            record_login_attempt(user, success=False, ip_address=get_user_ip())
            
            logger.warning(f"Failed login attempt for user {user.id} from IP {get_user_ip()}")
            return unauthorized_response("Invalid email or password")
        
        # Check if account is active
        if not user.is_active or user.deleted_at:
            logger.warning(f"Login attempt on deactivated account: {user.id}")
            return error_response("This account has been deactivated", status=403)
        
        # Check email verification (REQUIRED per user's preference)
        if not user.email_verified:
            logger.info(f"Login blocked - email not verified for user {user.id}")
            return error_response(
                "Please verify your email address before logging in. Check your inbox for the verification link.",
                status=403
            )
        
        # Successful authentication - record attempt
        record_login_attempt(user, success=True, ip_address=get_user_ip())
        
        # Create JWT tokens
        remember_me = validated_data.get('remember_me', False)
        
        # Token expiration
        access_expires = timedelta(hours=1)
        refresh_expires = timedelta(days=30 if remember_me else 7)
        
        access_token = create_access_token(
            identity=user.id,
            fresh=True,
            expires_delta=access_expires
        )
        
        refresh_token = create_refresh_token(
            identity=user.id,
            expires_delta=refresh_expires
        )
        
        # Log activity
        ActivityLog.log(
            action='user_login',
            user_id=user.id,
            entity_type='User',
            entity_id=user.id,
            description=f'User logged in from IP {get_user_ip()}',
            ip_address=get_user_ip(),
            user_agent=request.headers.get('User-Agent')
        )
        
        logger.info(f"Successful login for user {user.id}")
        
        # Prepare user data response
        user_data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email_verified': user.email_verified,
            'is_admin': user.is_admin,
            'profile_pic': user.profile_pic,
            'referral_code': user.referral_code
        }
        
        # Create response
        response_data = {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user_data
        }
        
        # Set HTTP-only cookies (for web clients)
        response = success_response(
            data=response_data,
            message='Login successful'
        )
        
        # Set cookies with secure flags
        set_access_cookies(response[0], access_token)
        set_refresh_cookies(response[0], refresh_token)
        
        return response
        
    except Exception as e:
        logger.error(f"Login error: {str(e)}", exc_info=True)
        return error_response("An error occurred during login. Please try again.", status=500)
