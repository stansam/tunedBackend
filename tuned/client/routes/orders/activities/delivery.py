"""
Delivery acceptance route for client blueprint.

Handles client acceptance of order deliveries with ratings and feedback.
"""

from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError
from datetime import datetime, timezone
import logging

from tuned.client import client_bp
from tuned.client.schemas import AcceptDeliverySchema
from tuned.models.order import Order
from tuned.models.user import User
from tuned.extensions import db
from tuned.utils import success_response, error_response, validation_error_response
from tuned.utils.decorators import rate_limit, log_activity
from tuned.services.notification_service import create_notification
from tuned.models.enums import NotificationType, OrderStatus

logger = logging.getLogger(__name__)


@client_bp.route('/orders/<int:order_id>/accept-delivery', methods=['POST'])
@jwt_required()
@rate_limit(max_requests=10, window=3600)
@log_activity('delivery_accepted', 'Order')
def accept_delivery(order_id):
    """
    Accept delivery of a completed order.
    
    Args:
        order_id: ID of the order
        
    Request Body:
        {
            "delivery_id": int,
            "rating": int (optional, 1-5),
            "feedback": str (optional, max 1000 chars)
        }
    
    Returns:
        200: Delivery accepted successfully
        404: Order not found
        403: Unauthorized access or order not delivered
        400: Validation error
    """
    current_user_id = get_jwt_identity()
    
    # Validate input
    schema = AcceptDeliverySchema()
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
        
        # Check if order is eligible for acceptance
        if order.status != OrderStatus.UNDER_REVIEW:
            return error_response(
                f'Cannot accept delivery for {order.status.value} orders',
                status=403
            )
        
        # Update order status to completed
        order.status = OrderStatus.COMPLETED
        order.delivered_at = datetime.now(timezone.utc)
        order.updated_at = datetime.now(timezone.utc)
        
        # Save rating and feedback if provided
        if data.get('rating'):
            # In a full implementation, save to OrderRating model
            logger.info(f'Order {order_id} rated: {data["rating"]}/5')
        
        if data.get('feedback'):
            # In a full implementation, save to OrderFeedback model
            logger.info(f'Feedback provided for order {order_id}')
        
        db.session.commit()
        
        logger.info(f'Delivery accepted for order {order_id} by user {current_user_id}')
        
        # Notify client
        try:
            create_notification(
                user_id=current_user_id,
                title='Order Completed',
                message=f'You have successfully accepted the delivery for "{order.title}"',
                type=NotificationType.SUCCESS,
                link=f'/orders/{order.id}'
            )
        except Exception as e:
            logger.error(f'Client notification error for delivery acceptance on order {order_id}: {str(e)}')
        
        # Notify admins and writer
        try:
            admins = User.query.filter_by(is_admin=True, is_active=True).all()
            for admin in admins:
                create_notification(
                    user_id=admin.id,
                    title=f'Delivery Accepted - {order.order_number}',
                    message=f'{order.client.get_name()} accepted delivery for "{order.title}"',
                    type=NotificationType.SUCCESS,
                    link=f'/admin/orders/{order.id}'
                )
            
            # Notify assigned writer
            if order.assigned_to:
                create_notification(
                    user_id=order.assigned_to,
                    title=f'Order Completed - {order.order_number}',
                    message=f'Client accepted your delivery for "{order.title}"',
                    type=NotificationType.SUCCESS,
                    link=f'/writer/orders/{order.id}'
                )
        except Exception as e:
            logger.error(f'Notification error for delivery acceptance on order {order_id}: {str(e)}')
        
        # Send emails
        try:
            from tuned.services.email_service import (
                send_order_completed_email_client,
                send_order_completed_email_admin
            )
            
            user = User.query.get(current_user_id)
            send_order_completed_email_client(user, order)
            send_order_completed_email_admin(order)
        except Exception as e:
            logger.error(f'Email error for delivery acceptance on order {order_id}: {str(e)}')
        
        # Prepare response
        delivery_data = {
            'order_id': order.id,
            'order_number': order.order_number,
            'status': order.status.value,
            'delivered_at': order.delivered_at.isoformat(),
            'rating': data.get('rating'),
            'feedback': data.get('feedback')
        }
        
        return success_response(
            data={'delivery': delivery_data},
            message='Delivery accepted successfully. Thank you for your business!'
        )
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error accepting delivery for order {order_id}: {str(e)}', exc_info=True)
        return error_response('An error occurred while accepting the delivery', status=500)
