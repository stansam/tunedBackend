"""
Referral code application and tracking routes for client blueprint.

Handles applying referral codes and viewing referral information.
"""

from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError
from datetime import datetime, timezone
from sqlalchemy import func
import logging

from tuned.client import client_bp
from tuned.client.schemas import ApplyReferralCodeSchema, ReferralFilterSchema
from tuned.models.user import User
from tuned.extensions import db
from tuned.utils import success_response, error_response, validation_error_response, created_response
from tuned.utils.decorators import rate_limit, log_activity
from tuned.services.notification_service import create_notification
from tuned.models.enums import NotificationType

logger = logging.getLogger(__name__)


@client_bp.route('/referrals/apply', methods=['POST'])
@jwt_required()
@rate_limit(max_requests=5, window=86400)  # 5 attempts per day
@log_activity('referral_code_applied', 'User')
def apply_referral_code():
    """
    Apply a referral code to current user's account.
    
    Request Body:
        {
            "referral_code": str (required, 6-20 chars)
        }
    
    Returns:
        201: Referral code applied successfully
        400: Invalid code, already used, or self-referral
        404: Code not found
    """
    current_user_id = get_jwt_identity()
    
    # Validate input
    schema = ApplyReferralCodeSchema()
    try:
        data = schema.load(request.get_json())
    except ValidationError as e:
        return validation_error_response(e.messages)
    
    try:
        user = User.query.get(current_user_id)
        
        if not user:
            return error_response('User not found', status=404)
        
        # Check if user already used a referral code
        # In a full implementation, check UserReferral model
        # For now, check a hypothetical field
        if hasattr(user, 'referred_by') and user.referred_by:
            return error_response('You have already applied a referral code', status=400)
        
        referral_code = data['referral_code'].upper()
        
        # Find referrer by code
        # In a full implementation, query ReferralCode model
        # For now, assume referral_code matches a user field
        referrer = User.query.filter(
            func.upper(User.referral_code) == referral_code
        ).first()
        
        if not referrer:
            return error_response('Invalid referral code', status=404)
        
        # Prevent self-referral
        if referrer.id == current_user_id:
            return error_response('You cannot use your own referral code', status=400)
        
        # Apply referral
        # In a full implementation, create UserReferral entry
        # Update user's referred_by field
        # Grant bonus points/credits to both users
        
        logger.info(f'Referral code applied: {referral_code} by user {current_user_id} (referrer: {referrer.id})')
        
        # Notify referrer
        try:
            create_notification(
                user_id=referrer.id,
                title='New Referral!',
                message=f'{user.get_name()} signed up using your referral code! You\'ve earned bonus points.',
                type=NotificationType.SUCCESS,
                link='/referrals'
            )
        except Exception as e:
            logger.error(f'Notification error for referral: {str(e)}')
        
        # Notify new user
        try:
            create_notification(
                user_id=current_user_id,
                title='Referral Bonus Received',
                message='Welcome! You\'ve received bonus points for using a referral code.',
                type=NotificationType.SUCCESS,
                link='/referrals'
            )
        except Exception as e:
            logger.error(f'Notification error for referral: {str(e)}')
        
        referral_data = {
            'referral_code': referral_code,
            'referrer_name': referrer.get_name(),
            'bonus_points': 100,  # Example bonus
            'applied_at': datetime.now(timezone.utc).isoformat()
        }
        
        return created_response(
            data={'referral': referral_data},
            message='Referral code applied successfully! You\'ve received 100 bonus points.'
        )
        
    except Exception as e:
        logger.error(f'Error applying referral code for user {current_user_id}: {str(e)}', exc_info=True)
        return error_response('An error occurred while applying the referral code', status=500)


@client_bp.route('/referrals/my-code', methods=['GET'])
@jwt_required()
@rate_limit(max_requests=100, window=60)
def get_my_referral_code():
    """
    Get current user's referral code.
    
    Returns:
        200: Referral code and statistics
    """
    current_user_id = get_jwt_identity()
    
    try:
        user = User.query.get(current_user_id)
        
        if not user:
            return error_response('User not found', status=404)
        
        # In a full implementation, query ReferralCode and UserReferral models
        # For now, generate/return a code based on user ID
        referral_code = user.referral_code or f'REF{user.id:06d}'
        
        # Get referral statistics
        # In a full implementation, count from UserReferral model
        total_referrals = 0
        active_referrals = 0
        total_earnings = 0.0
        
        code_data = {
            'referral_code': referral_code,
            'share_url': f'https://yourplatform.com/register?ref={referral_code}',
            'total_referrals': total_referrals,
            'active_referrals': active_referrals,
            'total_earnings': total_earnings,
            'pending_earnings': 0.0,
            'lifetime_points': 0
        }
        
        logger.info(f'Referral code retrieved for user {current_user_id}: {referral_code}')
        
        return success_response(
            data={'code': code_data},
            message='Referral code retrieved successfully'
        )
        
    except Exception as e:
        logger.error(f'Error retrieving referral code for user {current_user_id}: {str(e)}', exc_info=True)
        return error_response('An error occurred while retrieving your referral code', status=500)


@client_bp.route('/referrals/list', methods=['GET'])
@jwt_required()
@rate_limit(max_requests=100, window=60)
def get_referrals():
    """
    Get list of users referred by current user.
    
    Query Parameters:
        page: Page number (default: 1)
        per_page: Items per page (default: 10)
        status: Filter by referral status (pending, active, inactive)
        sort_by: Sort field (created_at, earnings)
        sort_order: Sort direction (asc, desc)
    
    Returns:
        200: List of referrals with pagination
    """
    current_user_id = get_jwt_identity()
    
    # Validate query parameters
    schema = ReferralFilterSchema()
    try:
        filters = schema.load(request.args.to_dict())
    except ValidationError as e:
        return validation_error_response(e.messages)
    
    try:
        # In a full implementation, query UserReferral model
        # For now, return empty list
        
        referrals_data = []
        
        response_data = {
            'referrals': referrals_data,
            'pagination': {
                'page': filters.get('page', 1),
                'per_page': filters.get('per_page', 10),
                'total': 0,
                'pages': 0,
                'has_next': False,
                'has_prev': False
            }
        }
        
        logger.info(f'Retrieved referrals for user {current_user_id}')
        
        return success_response(
            data=response_data,
            message='Referrals retrieved successfully'
        )
        
    except Exception as e:
        logger.error(f'Error retrieving referrals for user {current_user_id}: {str(e)}', exc_info=True)
        return error_response('An error occurred while retrieving your referrals', status=500)
