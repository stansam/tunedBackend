"""
Referral earnings and rewards routes for client blueprint.

Handles reward point redemption, earnings tracking, and withdrawals.
"""

from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError
from datetime import datetime, timezone
import logging

from tuned.client import client_bp
from tuned.client.schemas import (
    RedeemRewardSchema,
    ReferralEarningsSchema,
    WithdrawReferralEarningsSchema
)
from tuned.models.user import User
from tuned.models.order import Order
from tuned.extensions import db
from tuned.utils import success_response, error_response, validation_error_response, created_response
from tuned.utils.decorators import rate_limit, log_activity
from tuned.services.notification_service import create_notification
from tuned.models.enums import NotificationType

logger = logging.getLogger(__name__)


@client_bp.route('/referrals/redeem', methods=['POST'])
@jwt_required()
@rate_limit(max_requests=10, window=86400)  # 10 redemptions per day
@log_activity('reward_points_redeemed', 'User')
def redeem_reward_points():
    """
    Redeem reward points for discount on an order.
    
    Request Body:
        {
            "points": int (required, 100-100000, multiples of 100),
            "order_id": int (required)
        }
    
    Returns:
        201: Points redeemed successfully
        400: Insufficient points or invalid amount
        404: Order not found
    """
    current_user_id = get_jwt_identity()
    
    # Validate input
    schema = RedeemRewardSchema()
    try:
        data = schema.load(request.get_json())
    except ValidationError as e:
        return validation_error_response(e.messages)
    
    try:
        user = User.query.get(current_user_id)
        
        if not user:
            return error_response('User not found', status=404)
        
        # Verify order exists and belongs to user
        order = Order.query.filter_by(
            id=data['order_id'],
            client_id=current_user_id,
            is_deleted=False
        ).first()
        
        if not order:
            return error_response('Order not found', status=404)
        
        # Check if order is eligible for redemption
        if order.paid:
            return error_response('Cannot redeem points on paid orders', status=400)
        
        points_to_redeem = data['points']
        
        # In a full implementation, check user's available points
        # For now, assume user has points
        user_available_points = 1000  # Example
        
        if user_available_points < points_to_redeem:
            return error_response(
                f'Insufficient points. You have {user_available_points} points available.',
                status=400
            )
        
        # Calculate discount (e.g., 100 points = $1)
        discount_amount = points_to_redeem / 100
        
        # Apply discount to order
        order.discount_amount = (order.discount_amount or 0) + discount_amount
        order.total_price = order.total_price - discount_amount
        order.updated_at = datetime.now(timezone.utc)
        
        # In a full implementation, deduct points from user's balance
        # Create RewardRedemption record
        
        db.session.commit()
        
        logger.info(
            f'Reward points redeemed: {points_to_redeem} points (${discount_amount:.2f}) '
            f'for order {order.id} by user {current_user_id}'
        )
        
        # Notify user
        try:
            create_notification(
                user_id=current_user_id,
                title='Reward Points Redeemed',
                message=f'You redeemed {points_to_redeem} points for ${discount_amount:.2f} off your order.',
                type=NotificationType.SUCCESS,
                link=f'/orders/{order.id}'
            )
        except Exception as e:
            logger.error(f'Notification error for reward redemption: {str(e)}')
        
        redemption_data = {
            'points': points_to_redeem,
            'discount_amount': discount_amount,
            'order_id': order.id,
            'order_number': order.order_number,
            'new_total': float(order.total_price),
            'remaining_points': user_available_points - points_to_redeem,
            'redeemed_at': datetime.now(timezone.utc).isoformat()
        }
        
        return created_response(
            data={'redemption': redemption_data},
            message=f'Successfully redeemed {points_to_redeem} points for ${discount_amount:.2f} discount!'
        )
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error redeeming reward points for user {current_user_id}: {str(e)}', exc_info=True)
        return error_response('An error occurred while redeeming your points', status=500)


@client_bp.route('/referrals/earnings', methods=['GET'])
@jwt_required()
@rate_limit(max_requests=100, window=60)
def get_referral_earnings():
    """
    Get referral earnings summary and history.
    
    Query Parameters:
        from_date: Filter earnings from this date
        to_date: Filter earnings to this date
        status: Filter by status (pending, confirmed, withdrawn)
    
    Returns:
        200: Earnings summary and history
    """
    current_user_id = get_jwt_identity()
    
    # Validate query parameters
    schema = ReferralEarningsSchema()
    try:
        filters = schema.load(request.args.to_dict())
    except ValidationError as e:
        return validation_error_response(e.messages)
    
    try:
        # In a full implementation, query ReferralEarnings model
        # For now, return sample data
        
        earnings_data = {
            'summary': {
                'total_earnings': 0.0,
                'pending_earnings': 0.0,
                'confirmed_earnings': 0.0,
                'withdrawn_earnings': 0.0,
                'available_for_withdrawal': 0.0
            },
            'earnings_history': []
        }
        
        logger.info(f'Referral earnings retrieved for user {current_user_id}')
        
        return success_response(
            data={'earnings': earnings_data},
            message='Earnings retrieved successfully'
        )
        
    except Exception as e:
        logger.error(f'Error retrieving referral earnings for user {current_user_id}: {str(e)}', exc_info=True)
        return error_response('An error occurred while retrieving your earnings', status=500)


@client_bp.route('/referrals/withdraw', methods=['POST'])
@jwt_required()
@rate_limit(max_requests=5, window=86400)  # 5 withdrawals per day
@log_activity('referral_earnings_withdrawal_requested', 'User')
def request_withdrawal():
    """
    Request withdrawal of referral earnings.
    
    Request Body:
        {
            "amount": float (required, min 10.00),
            "payment_method": str (required: paypal, bank_transfer, store_credit),
            "payment_details": dict (required, e.g., PayPal email or bank account)
        }
    
    Returns:
        201: Withdrawal request submitted
        400: Insufficient balance or invalid amount
    """
    current_user_id = get_jwt_identity()
    
    # Validate input
    schema = WithdrawReferralEarningsSchema()
    try:
        data = schema.load(request.get_json())
    except ValidationError as e:
        return validation_error_response(e.messages)
    
    try:
        user = User.query.get(current_user_id)
        
        if not user:
            return error_response('User not found', status=404)
        
        withdrawal_amount = data['amount']
        payment_method = data['payment_method']
        payment_details = data['payment_details']
        
        # In a full implementation, check available balance
        available_balance = 0.0  # Example
        
        if available_balance < withdrawal_amount:
            return error_response(
                f'Insufficient balance. Available: ${available_balance:.2f}',
                status=400
            )
        
        # Create withdrawal request
        # In a full implementation, create WithdrawalRequest model entry
        
        logger.info(
            f'Withdrawal requested: ${withdrawal_amount:.2f} via {payment_method} '
            f'by user {current_user_id}'
        )
        
        # Notify user
        try:
            create_notification(
                user_id=current_user_id,
                title='Withdrawal Request Submitted',
                message=f'Your withdrawal request for ${withdrawal_amount:.2f} is being processed.',
                type=NotificationType.INFO,
                link='/referrals/earnings'
            )
        except Exception as e:
            logger.error(f'Notification error for withdrawal request: {str(e)}')
        
        withdrawal_data = {
            'amount': withdrawal_amount,
            'payment_method': payment_method,
            'status': 'pending',
            'requested_at': datetime.now(timezone.utc).isoformat(),
            'estimated_processing_days': 5-7
        }
        
        return created_response(
            data={'withdrawal': withdrawal_data},
            message='Withdrawal request submitted successfully. Processing typically takes 5-7 business days.'
        )
        
    except Exception as e:
        logger.error(f'Error processing withdrawal request for user {current_user_id}: {str(e)}', exc_info=True)
        return error_response('An error occurred while processing your withdrawal request', status=500)


@client_bp.route('/referrals/rewards-balance', methods=['GET'])
@jwt_required()
@rate_limit(max_requests=100, window=60)
def get_rewards_balance():
    """
    Get current reward points balance.
    
    Returns:
        200: Reward points balance and value
    """
    current_user_id = get_jwt_identity()
    
    try:
        # In a full implementation, query RewardPoints model
        # For now, return sample data
        
        balance_data = {
            'points_balance': 0,
            'points_value_usd': 0.0,  # 100 points = $1
            'pending_points': 0,
            'lifetime_points_earned': 0,
            'lifetime_points_redeemed': 0,
            'conversion_rate': '100 points = $1.00'
        }
        
        logger.info(f'Rewards balance retrieved for user {current_user_id}')
        
        return success_response(
            data={'balance': balance_data},
            message='Rewards balance retrieved successfully'
        )
        
    except Exception as e:
        logger.error(f'Error retrieving rewards balance for user {current_user_id}: {str(e)}', exc_info=True)
        return error_response('An error occurred while retrieving your balance', status=500)
