"""
Discount code validation route for client blueprint.

Handles discount code validation for orders.
"""

from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError
from datetime import datetime, timezone
import logging

from tuned.client import client_bp
from tuned.client.schemas import DiscountCodeSchema
from tuned.models.payment import Discount
from tuned.extensions import db
from tuned.utils import success_response, error_response, validation_error_response
from tuned.utils.decorators import rate_limit

logger = logging.getLogger(__name__)


@client_bp.route('/discounts/validate', methods=['POST'])
@jwt_required()
@rate_limit(max_requests=20, window=300)  # 20 validations per 5 minutes
def validate_discount_code():
    """
    Validate a discount code.
    
    Request Body:
        {
            "code": str (required, 3-50 chars),
            "order_total": float (optional, for percentage calculations)
        }
    
    Returns:
        200: Discount code valid with details
        400: Discount code invalid or expired
        422: Validation error
    """
    current_user_id = get_jwt_identity()
    
    # Validate input
    schema = DiscountCodeSchema()
    try:
        data = schema.load(request.get_json())
    except ValidationError as e:
        return validation_error_response(e.messages)
    
    try:
        code = data['code'].upper()
        order_total = data.get('order_total', 0)
        
        # Find discount code
        discount = Discount.query.filter_by(
            code=code,
            is_active=True
        ).first()
        
        if not discount:
            return error_response('Invalid discount code', status=400)
        
        # Check if discount is valid
        if not discount.is_valid():
            reasons = []
            
            if discount.start_date and discount.start_date > datetime.now(timezone.utc):
                reasons.append('Discount not yet active')
            
            if discount.end_date and discount.end_date < datetime.now(timezone.utc):
                reasons.append('Discount has expired')
            
            if discount.max_uses and discount.times_used >= discount.max_uses:
                reasons.append('Discount code has reached maximum uses')
            
            return error_response(
                f'Discount code is not valid: {", ".join(reasons)}',
                status=400
            )
        
        # Calculate discount amount
        if discount.discount_type.value == 'percentage':
            discount_amount = (discount.value / 100) * order_total if order_total else 0
            
            # Apply max discount limit if exists
            if discount.max_discount_amount and discount_amount > discount.max_discount_amount:
                discount_amount = discount.max_discount_amount
        else:  # fixed
            discount_amount = discount.value
        
        # Prepare response
        discount_data = {
            'code': discount.code,
            'type': discount.discount_type.value,
            'value': float(discount.value),
            'discount_amount': float(discount_amount) if order_total else None,
            'min_order_amount': float(discount.min_order_amount) if discount.min_order_amount else None,
            'max_discount_amount': float(discount.max_discount_amount) if discount.max_discount_amount else None,
            'valid_from': discount.start_date.isoformat() if discount.start_date else None,
            'valid_until': discount.end_date.isoformat() if discount.end_date else None,
            'remaining_uses': (discount.max_uses - discount.times_used) if discount.max_uses else None,
            'description': discount.description
        }
        
        logger.info(f'Discount code validated: {code} by user {current_user_id}')
        
        return success_response(
            data={'discount': discount_data},
            message=f'Discount code "{code}" is valid! You save ${discount_amount:.2f}' if order_total else f'Discount code "{code}" is valid!'
        )
        
    except Exception as e:
        logger.error(f'Error validating discount code: {str(e)}', exc_info=True)
        return error_response('An error occurred while validating the discount code', status=500)


@client_bp.route('/discounts/active', methods=['GET'])
@jwt_required()
@rate_limit(max_requests=50, window=3600)
def get_active_discounts():
    """
    Get list of publicly available active discount codes.
    
    Query Parameters:
        type: Filter by discount type (percentage, fixed)
    
    Returns:
        200: List of active public discounts
    """
    current_user_id = get_jwt_identity()
    
    try:
        discount_type = request.args.get('type')
        
        # Query active, public discounts
        query = Discount.query.filter_by(
            is_active=True,
            is_public=True
        ).filter(
            db.or_(
                Discount. end_date.is_(None),
                Discount.end_date > datetime.now(timezone.utc)
            )
        )
        
        if discount_type:
            query = query.filter_by(discount_type=discount_type)
        
        discounts = query.all()
        
        # Serialize discounts
        discounts_data = []
        for discount in discounts:
            if discount.is_valid():
                discounts_data.append({
                    'code': discount.code,
                    'description': discount.description,
                    'type': discount.discount_type.value,
                    'value': float(discount.value),
                    'min_order_amount': float(discount.min_order_amount) if discount.min_order_amount else None,
                    'valid_until': discount.end_date.isoformat() if discount.end_date else None
                })
        
        logger.info(f'Retrieved {len(discounts_data)} active discounts for user {current_user_id}')
        
        return success_response(
            data={'discounts': discounts_data},
            message=f'Found {len(discounts_data)} active discount codes'
        )
        
    except Exception as e:
        logger.error(f'Error retrieving active discounts: {str(e)}', exc_info=True)
        return error_response('An error occurred while retrieving discounts', status=500)
