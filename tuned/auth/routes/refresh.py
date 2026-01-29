"""
JWT token refresh route.

Handles refreshing access tokens using refresh tokens.
Provides secure token rotation for extended sessions.
"""
from flask import request
from flask_jwt_extended import (
    jwt_required,
    get_jwt_identity,
    create_access_token,
    get_jwt
)
from tuned.auth import auth_bp
from tuned.models.user import User
from tuned.utils import success_response, error_response, unauthorized_response
from tuned.models.audit import ActivityLog
from tuned.utils.auth import get_user_ip
from datetime import timedelta
import logging


logger = logging.getLogger(__name__)


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh_token():
    """
    Refresh access token using a valid refresh token.
    
    This endpoint allows clients to obtain a new access token without
    requiring the user to log in again, as long as they have a valid
    refresh token.
    
    **Security Features:**
    - Requires valid refresh token (not access token)
    - Verifies user account is still active
    - Verifies email is still verified
    - Checks if user account has been deleted
    - Logs refresh activity
    - Returns fresh=False token (cannot be used for sensitive operations)
    
    **Token Rotation:**
    By default, only returns a new access token. The refresh token remains valid.
    For enhanced security, you can implement refresh token rotation by also
    returning a new refresh token and blacklisting the old one.
    
    Headers:
        Authorization: Bearer <refresh_token>
    
    Returns:
        200: New access token generated successfully
        401: Invalid or expired refresh token
        403: Account deactivated or email not verified
        
    Example Response:
        {
            "success": true,
            "data": {
                "access_token": "eyJ0eXAi...",
                "token_type": "Bearer",
                "expires_in": 3600
            },
            "message": "Token refreshed successfully"
        }
    """
    try:
        # Get user identity from refresh token
        user_id = get_jwt_identity()
        jwt_data = get_jwt()
        
        # Verify this is actually a refresh token
        if jwt_data.get('type') != 'refresh':
            logger.warning(f"Attempted to use access token for refresh: user {user_id}")
            return unauthorized_response("Invalid token type. Refresh token required.")
        
        # Get user from database
        user = User.query.get(int(user_id))
        
        if not user:
            logger.warning(f"Refresh token used for non-existent user: {user_id}")
            return unauthorized_response("User not found")
        
        # Security checks
        if not user.is_active or user.deleted_at:
            logger.warning(f"Refresh token used for deactivated account: {user_id}")
            return error_response("Account is deactivated", status=403)
        
        if not user.email_verified:
            logger.warning(f"Refresh token used for unverified account: {user_id}")
            return error_response(
                "Email verification required. Please verify your email address.",
                status=403
            )
        
        # Create new access token (fresh=False)
        # Fresh tokens are only created during login with password
        access_token = create_access_token(
            identity=user.id,
            fresh=False,
            expires_delta=timedelta(hours=1)
        )
        
        # Optional: Implement refresh token rotation for enhanced security
        # Uncomment below to also return a new refresh token
        # new_refresh_token = create_refresh_token(
        #     identity=user.id,
        #     expires_delta=timedelta(days=7)
        # )
        # # Blacklist old refresh token
        # old_jti = jwt_data['jti']
        # from tuned.redis_client import add_token_to_blacklist
        # add_token_to_blacklist(old_jti, jwt_data['exp'] - time.time())
        
        # Log activity
        ActivityLog.log(
            action='token_refreshed',
            user_id=user.id,
            entity_type='User',
            entity_id=user.id,
            description=f'Access token refreshed from IP {get_user_ip()}',
            ip_address=get_user_ip(),
            user_agent=request.headers.get('User-Agent')
        )
        
        logger.info(f"Access token refreshed for user {user.id}")
        
        # Prepare response
        response_data = {
            'access_token': access_token,
            'token_type': 'Bearer',
            'expires_in': 3600  # 1 hour in seconds
        }
        
        # If implementing token rotation, add refresh_token to response
        # response_data['refresh_token'] = new_refresh_token
        
        return success_response(
            data=response_data,
            message='Token refreshed successfully'
        )
        
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}", exc_info=True)
        return error_response("An error occurred during token refresh", status=500)


@auth_bp.route('/verify-token', methods=['GET'])
@jwt_required()
def verify_token():
    """
    Verify if the current access token is valid.
    
    Useful for frontend to check if user is still authenticated
    without making a full API call.
    
    Headers:
        Authorization: Bearer <access_token>
    
    Returns:
        200: Token is valid, returns user info
        401: Token is invalid or expired
        
    Example Response:
        {
            "success": true,
            "data": {
                "user_id": 123,
                "email": "user@example.com",
                "email_verified": true,
                "is_admin": false,
                "token_type": "access",
                "fresh": false
            },
            "message": "Token is valid"
        }
    """
    try:
        # Get user identity
        user_id = get_jwt_identity()
        jwt_data = get_jwt()
        
        # Get user from database
        user = User.query.get(int(user_id))
        
        if not user:
            return unauthorized_response("User not found")
        
        # Check if account is active
        if not user.is_active or user.deleted_at:
            return error_response("Account is deactivated", status=403)
        
        # Prepare response data
        token_info = {
            'user_id': user.id,
            'username': user.username,
            'email': user.email,
            'email_verified': user.email_verified,
            'is_admin': user.is_admin,
            'token_type': jwt_data.get('type', 'unknown'),
            'fresh': jwt_data.get('fresh', False)
        }
        
        return success_response(
            data=token_info,
            message='Token is valid'
        )
        
    except Exception as e:
        logger.error(f"Token verification error: {str(e)}", exc_info=True)
        return error_response("An error occurred during token verification", status=500)
