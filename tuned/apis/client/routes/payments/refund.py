"""
Refund request route for client blueprint.

Handles client requests for payment refunds.
"""

from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError
from datetime import datetime, timezone
import logging

from tuned.client import client_bp
from tuned.client.schemas import RefundRequestSchema
from tuned.models.payment import Payment
from tuned.models.order import Order
from tuned.models.user import User
from tuned.extensions import db
from tuned.utils import success_response, error_response, validation_error_response, created_response
from tuned.utils.decorators import rate_limit, log_activity
from tuned.services.notification_service import create_notification
from tuned.models.enums import NotificationType, OrderStatus, PaymentStatus

logger = logging.getLogger(__name__)


@client_bp.route('/payments/<int:payment_id>/refund', methods=['POST'])
@jwt_required()
@rate_limit(max_requests=5, window=86400)  # 5 refund requests per day
@log_activity('refund_requested', 'Payment')
def request_refund(payment_id):
    """
    Request a refund for a payment.
    
    Args:
        payment_id: ID of the payment
        
    Request Body:
        {
            "reason": str (required, 20-500 chars),
            "refund_amount": float (optional, partial refund),
            "bank_details": dict (optional, for bank transfer refunds)
        }
    
    Returns:
        201: Refund request submitted successfully
        404: Payment not found
        403: Unauthorized access or payment not eligible
        400: Validation error
    """
    current_user_id = get_jwt_identity()
    
    # Validate input
    schema = RefundRequestSchema()
    try:
        data = schema.load(request.get_json())
    except ValidationError as e:
        return validation_error_response(e.messages)
    
    try:
        # Get payment and verify ownership through order
        payment = db.session.query(Payment).join(
            Payment.order
        ).filter(
            Payment.id == payment_id,
            Payment.order.has(client_id=current_user_id)
        ).first()
        
        if not payment:
            return error_response('Payment not found', status=404)
        
        # Check if payment is eligible for refund
        if payment.status.value != 'completed':
            return error_response(
                'Only completed payments can be refunded',
                status=403
            )
        
        # Check if refund amount is valid
        refund_amount = data.get('refund_amount', payment.amount)
        
        if refund_amount > payment.amount:
            return error_response(
                'Refund amount cannot exceed payment amount',
                status=400
            )
        
        if refund_amount <= 0:
            return error_response(
                'Refund amount must be greater than 0',
                status=400
            )
        
        # In a full implementation, create a Refund model entry
        # For now, log the request
        
        reason = data['reason']
        is_partial = refund_amount < payment.amount
        
        logger.info(
            f'Refund requested for payment {payment_id}: '
            f'${refund_amount:.2f} ({is_partial and "partial" or "full"}) '
            f'by user {current_user_id}. Reason: {reason[:50]}...'
        )
        
        # Notify client
        try:
            create_notification(
                user_id=current_user_id,
                title='Refund Request Submitted',
                message=f'Your refund request for ${refund_amount:.2f} has been submitted.',
                type=NotificationType.INFO,
                link=f'/payments/{payment.id}'
            )
        except Exception as e:
            logger.error(f'Client notification error for refund request on payment {payment_id}: {str(e)}')
        
        # Notify admins about refund request
        try:
            admins = User.query.filter_by(is_admin=True, is_active=True).all()
            for admin in admins:
                create_notification(
                    user_id=admin.id,
                    title=f'Refund Request - {payment.order.order_number}',
                    message=f'{payment.order.client.get_name()} requested ${refund_amount:.2f} refund. Reason: {reason[:50]}...',
                    type=NotificationType.WARNING,
                    link=f'/admin/payments/{payment.id}/refund'
                )
        except Exception as e:
            logger.error(f'Notification error for refund request on payment {payment_id}: {str(e)}')
        
        # Send email to finance team
        try:
            from tuned.services.email_service import send_refund_request_email_admin
            send_refund_request_email_admin(payment, refund_amount, reason)
        except Exception as e:
            logger.error(f'Email error for refund request on payment {payment_id}: {str(e)}')
        
        # Prepare response
        refund_data = {
            'payment_id': payment.id,
            'order_id': payment.order_id,
            'order_number': payment.order.order_number,
            'original_amount': float(payment.amount),
            'refund_amount': float(refund_amount),
            'is_partial': is_partial,
            'reason': reason,
            'status': 'pending_review',
            'requested_at': datetime.now(timezone.utc).isoformat()
        }
        
        return created_response(
            data={'refund_request': refund_data},
            message='Refund request submitted successfully. We will process your request within 5-7 business days.'
        )
        
    except Exception as e:
        logger.error(f'Error requesting refund for payment {payment_id}: {str(e)}', exc_info=True)
        return error_response('An error occurred while processing your refund request', status=500)


@client_bp.route('/payments/<int:payment_id>/refund-status', methods=['GET'])
@jwt_required()
@rate_limit(max_requests=100, window=60)
def get_refund_status(payment_id):
    """
    Get refund status for a payment.
    
    Args:
        payment_id: ID of the payment
    
    Returns:
        200: Refund status information
        404: Payment not found
        403: Unauthorized access
    """
    current_user_id = get_jwt_identity()
    
    try:
        # Get payment and verify ownership
        payment = db.session.query(Payment).join(
            Payment.order
        ).filter(
            Payment.id == payment_id,
            Payment.order.has(client_id=current_user_id)
        ).first()
        
        if not payment:
            return error_response('Payment not found', status=404)
        
        # In a full implementation, query Refund model
        # For now, return basic eligibility info
        
        refund_data = {
            'payment_id': payment.id,
            'payment_status': payment.status.value,
            'amount': float(payment.amount),
            'can_request_refund': payment.status.value == 'completed',
            'refund_policy': {
                'full_refund_days': 7,
                'partial_refund_days': 14,
                'processing_time_days': '5-7 business days'
            }
        }
        
        return success_response(
            data={'refund': refund_data},
            message='Refund status retrieved successfully'
        )
        
    except Exception as e:
        logger.error(f'Error getting refund status for payment {payment_id}: {str(e)}', exc_info=True)
        return error_response('An error occurred while retrieving refund status', status=500)
