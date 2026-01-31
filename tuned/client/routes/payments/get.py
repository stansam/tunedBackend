"""
Payment listing and details routes for client blueprint.

Handles retrieving payment information with filtering and pagination.
"""

from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError
import logging

from tuned.client import client_bp
from tuned.client.schemas import PaymentFilterSchema
from tuned.models.payment import Payment
from tuned.extensions import db
from tuned.utils import success_response, error_response, validation_error_response
from tuned.utils.decorators import rate_limit

logger = logging.getLogger(__name__)


@client_bp.route('/payments', methods=['GET'])
@jwt_required()
@rate_limit(max_requests=100, window=60)
def get_payments():
    """
    Get all payments for the authenticated client with filtering and pagination.
    
    Query Parameters:
        page: Page number (default: 1)
        per_page: Items per page (default: 10, max: 100)
        status: Filter by payment status
        method: Filter by payment method
        order_id: Filter by specific order
        sort_by: Sort field (created_at, amount, paid_at, status)
        sort_order: Sort direction (asc, desc)
        from_date: Filter payments created after this date
        to_date: Filter payments created before this date
    
    Returns:
        200: List of payments with pagination metadata
        400: Validation error
    """
    current_user_id = get_jwt_identity()
    
    # Validate query parameters
    schema = PaymentFilterSchema()
    try:
        filters = schema.load(request.args.to_dict())
    except ValidationError as e:
        logger.warning(f'Payment list validation failed for user {current_user_id}: {e.messages}')
        return validation_error_response(e.messages)
    
    try:
        # Build base query - get payments for user's orders
        query = db.session.query(Payment).join(
            Payment.order
        ).filter(
            Payment.order.has(client_id=current_user_id)
        )
        
        # Apply status filter
        if filters.get('status'):
            query = query.filter(Payment.status == filters['status'])
        
        # Apply payment method filter
        if filters.get('method'):
            query = query.filter(Payment.payment_method == filters['method'])
        
        # Apply order filter
        if filters.get('order_id'):
            query = query.filter(Payment.order_id == filters['order_id'])
        
        # Apply date range filters
        if filters.get('from_date'):
            query = query.filter(Payment.created_at >= filters['from_date'])
        
        if filters.get('to_date'):
            query = query.filter(Payment.created_at <= filters['to_date'])
        
        # Apply sorting
        sort_field = filters.get('sort_by', 'created_at')
        sort_order = filters.get('sort_order', 'desc')
        
        order_column = getattr(Payment, sort_field)
        if sort_order == 'desc':
            order_column = order_column.desc()
        else:
            order_column = order_column.asc()
        
        query = query.order_by(order_column)
        
        # Paginate results
        page = filters.get('page', 1)
        per_page = filters.get('per_page', 10)
        
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        # Serialize payments
        payments_data = []
        for payment in pagination.items:
            payments_data.append({
                'id': payment.id,
                'order_id': payment.order_id,
                'order_number': payment.order.order_number if payment.order else None,
                'amount': float(payment.amount),
                'currency': payment.currency.value if payment.currency else 'USD',
                'status': payment.status.value,
                'payment_method': payment.payment_method.value if payment.payment_method else None,
                'transaction_id': payment.transaction_id,
                'paid_at': payment.paid_at.isoformat() if payment.paid_at else None,
                'created_at': payment.created_at.isoformat()
            })
        
        # Prepare response
        response_data = {
            'payments': payments_data,
            'pagination': {
                'page': pagination.page,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        }
        
        logger.info(f'Retrieved {len(payments_data)} payments for user {current_user_id} (page {page})')
        
        return success_response(
            data=response_data,
            message=f'Retrieved {len(payments_data)} payments'
        )
        
    except Exception as e:
        logger.error(f'Error retrieving payments for user {current_user_id}: {str(e)}', exc_info=True)
        return error_response('An error occurred while retrieving your payments', status=500)


@client_bp.route('/payments/<int:payment_id>', methods=['GET'])
@jwt_required()
@rate_limit(max_requests=100, window=60)
def get_payment(payment_id):
    """
    Get detailed information about a specific payment.
    
    Args:
        payment_id: ID of the payment to retrieve
    
    Returns:
        200: Payment details
        404: Payment not found
        403: Unauthorized access
    """
    current_user_id = get_jwt_identity()
    
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
        
        # Serialize complete payment data
        payment_data = {
            'id': payment.id,
            'order_id': payment.order_id,
            'order_number': payment.order.order_number if payment.order else None,
            'amount': float(payment.amount),
            'currency': payment.currency.value if payment.currency else 'USD',
            'status': payment.status.value,
            'payment_method': payment.payment_method.value if payment.payment_method else None,
            'transaction_id': payment.transaction_id,
            'payer_email': payment.payer_email,
            'paid_at': payment.paid_at.isoformat() if payment.paid_at else None,
            'created_at': payment.created_at.isoformat(),
            'updated_at': payment.updated_at.isoformat() if payment.updated_at else None,
            'notes': payment.notes
        }
        
        logger.info(f'Retrieved payment {payment_id} for user {current_user_id}')
        
        return success_response(
            data={'payment': payment_data},
            message='Payment retrieved successfully'
        )
        
    except Exception as e:
        logger.error(f'Error retrieving payment {payment_id} for user {current_user_id}: {str(e)}', exc_info=True)
        return error_response('An error occurred while retrieving the payment', status=500)
