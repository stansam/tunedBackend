"""
User logout route.

Handles user logout with JWT token blacklisting (Redis-based).
"""
from flask import request
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from tuned.auth import auth_bp
from tuned.utils import success_response, error_response
from tuned.redis_client import add_token_to_blacklist
from tuned.models.audit import ActivityLog
from tuned.utils.auth import get_user_ip
import logging


logger = logging.getLogger(__name__)


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """
    Logout user by blacklisting their JWT tokens.
    
    Requires:
        - Valid JWT access token in Authorization header or cookies
    
    Returns:
        200: Logout successful
        401: Invalid or missing token
    """
    try:
        # Get JWT identity and token data
        user_id = get_jwt_identity()
        jwt_data = get_jwt()
        
        # Get JTI (JWT ID) for blacklisting
        jti = jwt_data['jti']
        token_type = jwt_data['type']  # 'access' or 'refresh'
        
        # Get token expiration time
        exp = jwt_data['exp']
        
        # Calculate time until expiration (for Redis TTL)
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).timestamp()
        expires_in = int(exp - now)
        
        # Add token to blacklist (Redis)
        if expires_in > 0:
            add_token_to_blacklist(jti, expires_in)
            logger.info(f"Token blacklisted for user {user_id}: {jti} (expires in {expires_in}s)")
        
        # Log activity
        ActivityLog.log(
            action='user_logout',
            user_id=user_id,
            entity_type='User',
            entity_id=user_id,
            description=f'User logged out from IP {get_user_ip()}',
            ip_address=get_user_ip(),
            user_agent=request.headers.get('User-Agent')
        )
        
        logger.info(f"User {user_id} logged out successfully")
        
        return success_response(
            message='Logout successful'
        )
        
    except Exception as e:
        logger.error(f"Logout error: {str(e)}", exc_info=True)
        return error_response("An error occurred during logout", status=500)
