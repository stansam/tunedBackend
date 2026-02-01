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
