"""
Support ticket route for client blueprint.

Handles creating support tickets for order-related issues.
"""

from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError
from datetime import datetime, timezone
import logging

from tuned.client import client_bp
from tuned.client.schemas import SupportTicketSchema
from tuned.models.order import Order
from tuned.models.user import User
from tuned.extensions import db
from tuned.utils import success_response, error_response, validation_error_response, created_response
from tuned.utils.decorators import rate_limit, log_activity
from tuned.services.notification_service import create_notification
from tuned.models.enums import NotificationType

logger = logging.getLogger(__name__)


@client_bp.route('/orders/<int:order_id>/support-ticket', methods=['POST'])
@jwt_required()
@rate_limit(max_requests=10, window=3600)  # 10 tickets per hour
@log_activity('support_ticket_created', 'Order')
def create_support_ticket(order_id):
    """
    Create a support ticket for an order.
    
    Args:
        order_id: ID of the order
        
    Request Body:
        {
            "subject": str (5-255 chars),
            "message": str (20-5000 chars),
            "priority": str (optional: low, normal, high, urgent)
        }
    
    Returns:
        201: Support ticket created successfully
        404: Order not found
        403: Unauthorized access
        400: Validation error
    """
    current_user_id = get_jwt_identity()
    
    # Validate input
    schema = SupportTicketSchema()
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
        
        priority = data.get('priority', 'normal')
        
        logger.info(
            f'Support ticket created for order {order_id} by user {current_user_id}: '
            f'"{data["subject"]}" (Priority: {priority})'
        )
        
        # Notify admins about support ticket
        try:
            admins = User.query.filter_by(is_admin=True, is_active=True).all()
            notification_type = NotificationType.URGENT if priority == 'urgent' else NotificationType.WARNING
            
            for admin in admins:
                create_notification(
                    user_id=admin.id,
                    title=f'Support Ticket - {order.order_number}',
                    message=f'[{priority.upper()}] {data["subject"]} - {order.client.get_name()}',
                    type=notification_type,
                    link=f'/admin/orders/{order.id}/support'
                )
        except Exception as e:
            logger.error(f'Notification error for support ticket on order {order_id}: {str(e)}')
        
        # Send email to support team
        try:
            from tuned.services.email_service import send_support_ticket_email_admin
            send_support_ticket_email_admin(order, data['subject'], data['message'], priority)
        except Exception as e:
            logger.error(f'Email error for support ticket on order {order_id}: {str(e)}')
        
        # In a full implementation, you might create a separate SupportTicket model
        # For now, we'll just log and notify
        
        # Prepare response
        ticket_data = {
            'order_id': order.id,
            'order_number': order.order_number,
            'subject': data['subject'],
            'message': data['message'],
            'priority': priority,
            'status': 'open',
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        
        return created_response(
            data={'ticket': ticket_data},
            message='Support ticket created successfully. Our team will respond within 24 hours.'
        )
        
    except Exception as e:
        logger.error(f'Error creating support ticket for order {order_id}: {str(e)}', exc_info=True)
        return error_response('An error occurred while creating the support ticket', status=500)
