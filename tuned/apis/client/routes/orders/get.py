"""
Order listing route for client blueprint.

Handles retrieving the authenticated client's orders with filtering,
sorting, and pagination.
"""

from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError
from sqlalchemy import or_
import logging

from tuned.client import client_bp
from tuned.client.schemas import OrderFilterSchema
from tuned.models.order import Order
from tuned.models.service import Service, AcademicLevel, Deadline
from tuned.utils import success_response, error_response, validation_error_response
from tuned.utils.decorators import rate_limit

logger = logging.getLogger(__name__)


@client_bp.route('/orders', methods=['GET'])
@jwt_required()
@rate_limit(max_requests=100, window=60)  # 100 requests per minute
def get_orders():
    """
    Get all orders for the authenticated client with filtering and pagination.
    
    Query Parameters:
        page: Page number (default: 1)
        per_page: Items per page (default: 10, max: 100)
        status: Filter by order status
        search: Search by title or order number
        sort_by: Sort field (created_at, due_date, total_price, status, title, updated_at)
        sort_order: Sort direction (asc, desc)
        from_date: Filter orders created after this date (ISO format)
        to_date: Filter orders created before this date (ISO format)
    
    Returns:
        200: List of orders with pagination metadata
        400: Validation error
    """
    current_user_id = get_jwt_identity()
    
    # Validate query parameters
    schema = OrderFilterSchema()
    try:
        filters = schema.load(request.args.to_dict())
    except ValidationError as e:
        logger.warning(f'Order list validation failed for user {current_user_id}: {e.messages}')
        return validation_error_response(e.messages)
    
    try:
        # Build base query for current user's orders
        query = Order.query.filter_by(
            client_id=current_user_id,
            is_deleted=False
        )
        
        # Apply status filter
        if filters.get('status'):
            query = query.filter(Order.status == filters['status'])
        
        # Apply search filter
        if filters.get('search'):
            search_term = f"%{filters['search']}%"
            query = query.filter(
                or_(
                    Order.title.ilike(search_term),
                    Order.order_number.ilike(search_term),
                    Order.description.ilike(search_term)
                )
            )
        
        # Apply date range filters
        if filters.get('from_date'):
            query = query.filter(Order.created_at >= filters['from_date'])
        
        if filters.get('to_date'):
            query = query.filter(Order.created_at <= filters['to_date'])
        
        # Apply sorting
        sort_field = filters.get('sort_by', 'created_at')
        sort_order = filters.get('sort_order', 'desc')
        
        order_column = getattr(Order, sort_field)
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
        
        # Serialize orders
        orders_data = []
        for order in pagination.items:
            orders_data.append({
                'id': order.id,
                'order_number': order.order_number,
                'title': order.title,
                'service': {
                    'id': order.service.id,
                    'name': order.service.name
                } if order.service else None,
                'academic_level': {
                    'id': order.academic_level.id,
                    'name': order.academic_level.name
                } if order.academic_level else None,
                'deadline': {
                    'id': order.deadline.id,
                    'name': order.deadline.name
                } if order.deadline else None,
                'total_price': float(order.total_price),
                'currency': order.currency.value if order.currency else 'USD',
                'status': order.status.value,
                'paid': order.paid,
                'due_date': order.due_date.isoformat() if order.due_date else None,
                'created_at': order.created_at.isoformat(),
                'updated_at': order.updated_at.isoformat() if order.updated_at else None
            })
        
        # Prepare response
        response_data = {
            'orders': orders_data,
            'pagination': {
                'page': pagination.page,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        }
        
        logger.info(f'Retrieved {len(orders_data)} orders for user {current_user_id} (page {page})')
        
        return success_response(
            data=response_data,
            message=f'Retrieved {len(orders_data)} orders'
        )
        
    except Exception as e:
        logger.error(f'Error retrieving orders for user {current_user_id}: {str(e)}', exc_info=True)
        return error_response('An error occurred while retrieving your orders', status=500)


@client_bp.route('/orders/<int:order_id>', methods=['GET'])
@jwt_required()
@rate_limit(max_requests=100, window=60)
def get_order(order_id):
    """
    Get detailed information about a specific order.
    
    Args:
        order_id: ID of the order to retrieve
    
    Returns:
        200: Order details
        404: Order not found
        403: Unauthorized access
    """
    current_user_id = get_jwt_identity()
    
    try:
        # Get order and verify ownership
        order = Order.query.filter_by(
            id=order_id,
            client_id=current_user_id,
            is_deleted=False
        ).first()
        
        if not order:
            return error_response('Order not found', status=404)
        
        # Serialize complete order data
        order_data = {
            'id': order.id,
            'order_number': order.order_number,
            'title': order.title,
            'description': order.description,
            'service': {
                'id': order.service.id,
                'name': order.service.name,
                'description': order.service.description
            } if order.service else None,
            'academic_level': {
                'id': order.academic_level.id,
                'name': order.academic_level.name
            } if order.academic_level else None,
            'deadline': {
                'id': order.deadline.id,
                'name': order.deadline.name,
                'hours': order.deadline.hours
            } if order.deadline else None,
            'word_count': order.word_count,
            'page_count': float(order.page_count) if order.page_count else None,
            'format_style': order.format_style,
            'report_type': order.report_type,
            'additional_materials': order.additional_materials,
            'price_per_page': float(order.price_per_page),
            'subtotal': float(order.subtotal),
            'discount_amount': float(order.discount_amount) if order.discount_amount else 0.0,
            'total_price': float(order.total_price),
            'currency': order.currency.value if order.currency else 'USD',
            'status': order.status.value,
            'paid': order.paid,
            'due_date': order.due_date.isoformat() if order.due_date else None,
            'created_at': order.created_at.isoformat(),
            'updated_at': order.updated_at.isoformat() if order.updated_at else None,
            'delivered_at': order.delivered_at.isoformat() if order.delivered_at else None
        }
        
        logger.info(f'Retrieved order {order_id} for user {current_user_id}')
        
        return success_response(
            data={'order': order_data},
            message='Order retrieved successfully'
        )
        
    except Exception as e:
        logger.error(f'Error retrieving order {order_id} for user {current_user_id}: {str(e)}', exc_info=True)
        return error_response('An error occurred while retrieving the order', status=500)
