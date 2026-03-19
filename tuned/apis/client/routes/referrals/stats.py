"""
Referral sharing and statistics routes for client blueprint.

Handles social media sharing and comprehensive referral statistics.
"""

from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError
from datetime import datetime, timezone, timedelta
import logging

from tuned.client import client_bp
from tuned.client.schemas import ReferralShareSchema, ReferralStatsFilterSchema
from tuned.models.user import User
from tuned.extensions import db
from tuned.utils import success_response, error_response, validation_error_response, created_response
from tuned.utils.decorators import rate_limit, log_activity

logger = logging.getLogger(__name__)


@client_bp.route('/referrals/share', methods=['POST'])
@jwt_required()
@rate_limit(max_requests=50, window=3600)  # 50 shares per hour
@log_activity('referral_shared', 'User')
def share_referral():
    """
    Generate shareable content for social media platforms.
    
    Request Body:
        {
            "platform": str (required: facebook, twitter, linkedin, whatsapp, email, copy_link),
            "message": str (optional, custom message)
        }
    
    Returns:
        200: Shareable content generated
    """
    current_user_id = get_jwt_identity()
    
    # Validate input
    schema = ReferralShareSchema()
    try:
        data = schema.load(request.get_json())
    except ValidationError as e:
        return validation_error_response(e.messages)
    
    try:
        user = User.query.get(current_user_id)
        
        if not user:
            return error_response('User not found', status=404)
        
        # Get user's referral code
        referral_code = user.referral_code or f'REF{user.id:06d}'
        platform = data['platform']
        custom_message = data.get('message')
        
        # Base share URL
        share_url = f'https://yourplatform.com/register?ref={referral_code}'
        
        # Default message
        default_message = (
            f"Join me on this amazing platform! Use my referral code {referral_code} "
            "and get bonus points on signup. Start your journey today!"
        )
        
        message = custom_message or default_message
        
        # Generate platform-specific share content
        if platform == 'facebook':
            share_link = f'https://www.facebook.com/sharer/sharer.php?u={share_url}&quote={message}'
        elif platform == 'twitter':
            share_link = f'https://twitter.com/intent/tweet?text={message}&url={share_url}'
        elif platform == 'linkedin':
            share_link = f'https://www.linkedin.com/sharing/share-offsite/?url={share_url}'
        elif platform == 'whatsapp':
            share_link = f'https://wa.me/?text={message}%20{share_url}'
        elif platform == 'email':
            subject = 'Join me on this amazing platform!'
            body = f'{message}\n\nSign up here: {share_url}'
            share_link = f'mailto:?subject={subject}&body={body}'
        else:  # copy_link
            share_link = share_url
        
        # In a full implementation, track share event
        logger.info(f'Referral shared via {platform} by user {current_user_id}')
        
        share_data = {
            'platform': platform,
            'share_link': share_link,
            'referral_code': referral_code,
            'share_url': share_url,
            'message': message
        }
        
        return success_response(
            data={'share': share_data},
            message='Share content generated successfully'
        )
        
    except Exception as e:
        logger.error(f'Error generating share content for user {current_user_id}: {str(e)}', exc_info=True)
        return error_response('An error occurred while generating share content', status=500)


@client_bp.route('/referrals/statistics', methods=['GET'])
@jwt_required()
@rate_limit(max_requests=100, window=60)
def get_referral_statistics():
    """
    Get comprehensive referral statistics and dashboard data.
    
    Query Parameters:
        period: Time period (7d, 30d, 90d, 1y, all)
        metric: Specific metric to focus on (referrals, earnings, conversions)
    
    Returns:
        200: Comprehensive referral statistics
    """
    current_user_id = get_jwt_identity()
    
    # Validate query parameters
    schema = ReferralStatsFilterSchema()
    try:
        filters = schema.load(request.args.to_dict())
    except ValidationError as e:
        return validation_error_response(e.messages)
    
    try:
        period = filters.get('period', '30d')
        
        # Calculate date range
        now = datetime.now(timezone.utc)
        if period == '7d':
            start_date = now - timedelta(days=7)
        elif period == '30d':
            start_date = now - timedelta(days=30)
        elif period == '90d':
            start_date = now - timedelta(days=90)
        elif period == '1y':
            start_date = now - timedelta(days=365)
        else:  # all
            start_date = None
        
        # In a full implementation, query ReferralStats, UserReferral, ReferralEarnings models
        # For now, return sample comprehensive data
        
        statistics = {
            'overview': {
                'total_referrals': 0,
                'active_referrals': 0,
                'conversion_rate': 0.0,
                'total_earnings': 0.0,
                'pending_earnings': 0.0,
                'reward_points_earned': 0
            },
            'period_stats': {
                'period': period,
                'start_date': start_date.isoformat() if start_date else None,
                'end_date': now.isoformat(),
                'new_referrals': 0,
                'period_earnings': 0.0
            },
            'performance': {
                'click_through_rate': 0.0,
                'signup_conversion_rate': 0.0,
                'purchase_conversion_rate': 0.0,
                'average_order_value': 0.0
            },
            'top_referrals': [],  # Top 5 referrals by earnings
            'recent_activity': [],  # Last 10 referral activities
            'earnings_breakdown': {
                'signup_bonuses': 0.0,
                'order_commissions': 0.0,
                'milestone_bonuses': 0.0
            },
            'share_stats': {
                'total_shares': 0,
                'shares_by_platform': {
                    'facebook': 0,
                    'twitter': 0,
                    'whatsapp': 0,
                    'email': 0,
                    'link_copy': 0
                }
            }
        }
        
        logger.info(f'Referral statistics retrieved for user {current_user_id} (period: {period})')
        
        return success_response(
            data={'statistics': statistics},
            message='Referral statistics retrieved successfully'
        )
        
    except Exception as e:
        logger.error(f'Error retrieving referral statistics for user {current_user_id}: {str(e)}', exc_info=True)
        return error_response('An error occurred while retrieving referral statistics', status=500)


@client_bp.route('/referrals/leaderboard', methods=['GET'])
@jwt_required()
@rate_limit(max_requests=50, window=3600)
def get_referral_leaderboard():
    """
    Get referral program leaderboard.
    
    Query Parameters:
        period: Time period (week, month, year, all)
        limit: Number of top referrers to show (default: 10, max: 100)
    
    Returns:
        200: Leaderboard data
    """
    current_user_id = get_jwt_identity()
    
    try:
        period = request.args.get('period', 'month')
        limit = min(int(request.args.get('limit', 10)), 100)
        
        # In a full implementation, query and rank users by referrals/earnings
        # For now, return sample data
        
        leaderboard_data = {
            'period': period,
            'your_rank': None,
            'top_referrers': [],
            'total_participants': 0,
            'updated_at': datetime.now(timezone.utc).isoformat()
        }
        
        logger.info(f'Referral leaderboard retrieved for user {current_user_id}')
        
        return success_response(
            data={'leaderboard': leaderboard_data},
            message='Leaderboard retrieved successfully'
        )
        
    except Exception as e:
        logger.error(f'Error retrieving leaderboard for user {current_user_id}: {str(e)}', exc_info=True)
        return error_response('An error occurred while retrieving the leaderboard', status=500)


@client_bp.route('/referrals/program-info', methods=['GET'])
@jwt_required()
@rate_limit(max_requests=100, window=60)
def get_referral_program_info():
    """
    Get referral program information and terms.
    
    Returns:
        200: Program information, rewards structure, and terms
    """
    current_user_id = get_jwt_identity()
    
    try:
        program_info = {
            'rewards_structure': {
                'signup_bonus': {
                    'referrer': 100,  # points
                    'referee': 50  # points
                },
                'first_order_commission': 10,  # percentage
                'ongoing_commission': 5,  # percentage
                'milestone_bonuses': [
                    {'referrals': 5, 'bonus': 500},
                    {'referrals': 10, 'bonus': 1500},
                    {'referrals': 25, 'bonus': 5000}
                ]
            },
            'points_conversion': {
                'rate': '100 points = $1.00',
                'minimum_redemption': 100,
                'maximum_redemption': 100000
            },
            'withdrawal_info': {
                'minimum_amount': 10.00,
                'processing_time': '5-7 business days',
                'payment_methods': ['PayPal', 'Bank Transfer', 'Store Credit']
            },
            'terms': {
                'commission_validity': '30 days from signup',
                'fraud_policy': 'Self-referrals and fake accounts are prohibited',
                'payout_threshold': 10.00
            }
        }
        
        logger.info(f'Referral program info retrieved for user {current_user_id}')
        
        return success_response(
            data={'program': program_info},
            message='Referral program information retrieved successfully'
        )
        
    except Exception as e:
        logger.error(f'Error retrieving program info for user {current_user_id}: {str(e)}', exc_info=True)
        return error_response('An error occurred while retrieving program information', status=500)
