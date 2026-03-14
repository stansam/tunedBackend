"""
Revision request route for client blueprint.

Handles client requests for order revisions.
"""

from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError
from datetime import datetime, timezone
import logging

from tuned.client import client_bp
from tuned.client.schemas import RequestRevisionSchema
from tuned.models.order import Order
from tuned.models.user import User
from tuned.extensions import db
from tuned.utils import success_response, error_response, validation_error_response, created_response
from tuned.utils.decorators import rate_limit, log_activity
from tuned.services.notification_service import create_notification
from tuned.models.enums import NotificationType, OrderStatus

logger = logging.getLogger(__name__)


@client_bp.route('/orders/<int:order_id>/request-revision', methods=['POST'])
@jwt_required()
@rate_limit(max_requests=5, window=86400)  # 5 revision requests per day
@log_activity('revision_requested', 'Order')
def request_revision(order_id):
    """
    Request a revision for a delivered order.
    
    Args:
        order_id: ID of the order
        
    Request Body:
        {
            "delivery_id": int,
            "revision_notes": str (20-2000 chars)
        }
    
    Returns:
        201: Revision request submitted successfully
        404: Order not found
        403: Unauthorized access or order not eligible
        400: Validation error
    """
    current_user_id = get_jwt_identity()
    
    # Validate input
    schema = RequestRevisionSchema()
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
        
        # Check if order is eligible for revision
        if order.status not in [OrderStatus.UNDER_REVIEW, OrderStatus.COMPLETED]:
            return error_response(
                f'Cannot request revision for {order.status.value} orders',
                status=403
            )
        
        if not order.paid:
            return error_response(
                'Cannot request revision for unpaid orders',
                status=403
            )
        
        # In a full implementation, verify delivery_id exists and belongs to this order
        delivery_id = data['delivery_id']
        revision_notes = data['revision_notes']
        
        # Update order status to revision
        order.status = OrderStatus.REVISION
        order.updated_at = datetime.now(timezone.utc)
        
        db.session.commit()
        
        logger.info(
            f'Revision requested for order {order_id} (delivery {delivery_id}) '
            f'by user {current_user_id}'
        )
        
        # Notify client
        try:
            create_notification(
                user_id=current_user_id,
                title='Revision Request Submitted',
                message=f'Your revision request for order "{order.title}" has been submitted.',
                type=NotificationType.INFO,
                link=f'/orders/{order.id}'
            )
        except Exception as e:
            logger.error(f'Client notification error for revision on order {order_id}: {str(e)}')
        
        # Notify admins about the revision request
        try:
            admins = User.query.filter_by(is_admin=True, is_active=True).all()
            for admin in admins:
                create_notification(
                    user_id=admin.id,
                    title=f'Revision Request - {order.order_number}',
                    message=f'{order.client.get_name()} requested revisions for "{order.title}"',
                    type=NotificationType.WARNING,
                    link=f'/admin/orders/{order.id}'
                )
        except Exception as e:
            logger.error(f'Notification error for revision on order {order_id}: {str(e)}')
        
        # Send emails
        try:
            from tuned.services.email_service import send_revision_request_email_admin
            send_revision_request_email_admin(order, revision_notes)
        except Exception as e:
            logger.error(f'Email error for revision on order {order_id}: {str(e)}')
        
        # Prepare response
        revision_data = {
            'order_id': order.id,
            'order_number': order.order_number,
            'delivery_id': delivery_id,
            'revision_notes': revision_notes,
            'status': order.status.value,
            'requested_at': datetime.now(timezone.utc).isoformat()
        }
        
        return created_response(
            data={'revision_request': revision_data},
            message='Revision request submitted successfully. Your writer will review and make the necessary changes.'
        )
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error requesting revision for order {order_id}: {str(e)}', exc_info=True)
        return error_response('An error occurred while processing your revision request', status=500)
