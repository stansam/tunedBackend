"""
Deadline extension route for client blueprint.

Handles client requests for order deadline extensions.
"""

from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError
from datetime import datetime, timedelta, timezone
import logging

from tuned.client import client_bp
from tuned.client.schemas import ExtendDeadlineSchema
from tuned.models.order import Order
from tuned.models.user import User
from tuned.extensions import db
from tuned.utils import success_response, error_response, validation_error_response, created_response
from tuned.utils.decorators import rate_limit, log_activity
from tuned.services.notification_service import create_notification
from tuned.models.enums import NotificationType, OrderStatus

logger = logging.getLogger(__name__)


@client_bp.route('/orders/<int:order_id>/extend-deadline', methods=['POST'])
@jwt_required()
@rate_limit(max_requests=5, window=86400)  # 5 extension requests per day per order
@log_activity('deadline_extension_requested', 'Order')
def request_deadline_extension(order_id):
    """
    Request a deadline extension for an order.
    
    Args:
        order_id: ID of the order
        
    Request Body:
        {
            "requested_hours": int (12-720),
            "reason": str (20-500 chars)
        }
    
    Returns:
        201: Extension request submitted successfully
        404: Order not found
        403: Unauthorized access or order not eligible
        400: Validation error
    """
    current_user_id = get_jwt_identity()
    
    # Validate input
    schema = ExtendDeadlineSchema()
    try:
        data = schema.load(request.get_json())
    except ValidationError as e:
        return validation_error_response(e.messages)
    
    try:
        # Verify order exists and user has access
        order = Order.query.filter_by(
            id=order_id,
            client_id=current_user_id,
            is_deleted=False
        ).first()
        
        if not order:
            return error_response('Order not found', status=404)
        
        # Check if order is eligible for extension
        if order.status in [OrderStatus.COMPLETED, OrderStatus.CANCELLED, OrderStatus.REFUNDED]:
            return error_response(
                f'Cannot extend deadline for {order.status.value} orders',
                status=403
            )
        
        if not order.paid:
            return error_response(
                'Please complete payment before requesting a deadline extension',
                status=403
            )
        
        # Calculate new due date
        new_due_date = order.due_date + timedelta(hours=data['requested_hours'])
        extension_hours = data['requested_hours']
        
        # Store the extension request in order notes or create a notification
        # (In a full implementation, you might create a separate DeadlineExtensionRequest model)
        
        logger.info(
            f'Deadline extension requested for order {order_id}: '
            f'{extension_hours} hours by user {current_user_id}'
        )
        
        # Notify admins about extension request
        try:
            admins = User.query.filter_by(is_admin=True, is_active=True).all()
            for admin in admins:
                create_notification(
                    user_id=admin.id,
                    title=f'Deadline Extension Request - {order.order_number}',
                    message=f'{order.client.get_name()} requested {extension_hours}h extension for "{order.title}". Reason: {data["reason"][:50]}...',
                    type=NotificationType.WARNING,
                    link=f'/admin/orders/{order.id}'
                )
        except Exception as e:
            logger.error(f'Notification error for extension request on order {order_id}: {str(e)}')
        
        # Send email to admins
        try:
            from tuned.services.email_service import send_deadline_extension_request_email_admin
            send_deadline_extension_request_email_admin(order, extension_hours, data['reason'])
        except Exception as e:
            logger.error(f'Email error for extension request on order {order_id}: {str(e)}')
        
        # Prepare response
        response_data = {
            'order_id': order.id,
            'order_number': order.order_number,
            'current_due_date': order.due_date.isoformat(),
            'requested_extension_hours': extension_hours,
            'requested_new_due_date': new_due_date.isoformat(),
            'reason': data['reason'],
            'status': 'pending_admin_approval'
        }
        
        return created_response(
            data={'extension_request': response_data},
            message='Deadline extension request submitted. An admin will review your request shortly.'
        )
        
    except Exception as e:
        logger.error(f'Error requesting deadline extension for order {order_id}: {str(e)}', exc_info=True)
        return error_response('An error occurred while processing your extension request', status=500)


@client_bp.route('/orders/<int:order_id>/deadline-status', methods=['GET'])
@jwt_required()
@rate_limit(max_requests=100, window=60)
def get_deadline_status(order_id):
    """
    Get the current deadline status for an order.
    
    Args:
        order_id: ID of the order
    
    Returns:
        200: Deadline status information
        404: Order not found
        403: Unauthorized access
    """
    current_user_id = get_jwt_identity()
    
    try:
        # Verify order exists and user has access
        order = Order.query.filter_by(
            id=order_id,
            client_id=current_user_id,
            is_deleted=False
        ).first()
        
        if not order:
            return error_response('Order not found', status=404)
        
        # Calculate time remaining
        now = datetime.now(timezone.utc)
        time_remaining = order.due_date - now if order.due_date > now else timedelta(0)
        hours_remaining = int(time_remaining.total_seconds() / 3600)
        is_overdue = order.due_date < now
        
        # Prepare response
        deadline_data = {
            'order_id': order.id,
            'order_number': order.order_number,
            'due_date': order.due_date.isoformat(),
            'hours_remaining': hours_remaining if not is_overdue else 0,
            'is_overdue': is_overdue,
            'days_remaining': hours_remaining // 24 if not is_overdue else 0,
            'status': order.status.value,
            'can_request_extension': order.paid and order.status not in [
                OrderStatus.COMPLETED, OrderStatus.CANCELLED, OrderStatus.REFUNDED
            ]
        }
        
        return success_response(
            data={'deadline': deadline_data},
            message='Deadline status retrieved successfully'
        )
        
    except Exception as e:
        logger.error(f'Error retrieving deadline status for order {order_id}: {str(e)}', exc_info=True)
        return error_response('An error occurred while retrieving deadline status', status=500)
