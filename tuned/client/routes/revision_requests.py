"""
Client routes for revision request management.

Handles creation, listing, and cancellation of revision requests.
"""
from flask import request, g
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError
from datetime import datetime, timezone
import logging

from tuned.client import client_bp
from tuned.client.schemas import CreateRevisionRequestSchema
from tuned.models.order import Order
from tuned.models.revision_request import OrderRevisionRequest
from tuned.models.order_delivery import OrderDelivery
from tuned.models.user import User
from tuned.models.enums import OrderStatus, RevisionRequestStatus
from tuned.extensions import db
from tuned.utils import (
    success_response,
    error_response,
    validation_error_response,
    created_response
)
from tuned.utils.decorators import rate_limit, log_activity, require_resource_ownership
from tuned.services.notification_service import create_notification
from tuned.models.enums import NotificationType

logger = logging.getLogger(__name__)


@client_bp.route('/orders/<int:order_id>/revision-requests', methods=['POST'])
@jwt_required()
@rate_limit(max_requests=5, window=86400)  # 5 requests per day
@log_activity('revision_request_created', 'OrderRevisionRequest')
def create_revision_request(order_id):
    """
    Create a new revision request for a delivered order.
    
    Client can request revisions after receiving delivery,
    specifying what needs to be changed/improved.
    
    Request Body:
        {
            "delivery_id": int (required),
            "revision_notes": str (required, 20-2000 chars)
        }
    
    Returns:
        201: Revision request created successfully
        400: Validation error
        403: Order not eligible for revision
        404: Order or delivery not found
    """
    current_user_id = int(get_jwt_identity())
    
    # Validate request data
    schema = CreateRevisionRequestSchema()
    try:
        data = schema.load(request.get_json())
    except ValidationError as e:
        return validation_error_response(e.messages)
    
    try:
        # Verify order exists and user owns it
        order = Order.query.filter_by(
            id=order_id,
            client_id=current_user_id,
            is_deleted=False
        ).first()
        
        if not order:
            return error_response('Order not found', status=404)
        
        # Verify order is eligible for revision
        if order.status not in [OrderStatus.COMPLETED_PENDING_REVIEW, OrderStatus.COMPLETED]:
            return error_response(
                f'Cannot request revision for orders with status: {order.status.value}',
                status=403
            )
        
        if not order.paid:
            return error_response('Cannot request revision for unpaid orders', status=403)
        
        # Verify delivery exists and belongs to this order
        delivery = OrderDelivery.query.filter_by(
            id=data['delivery_id'],
            order_id=order_id
        ).first()
        
        if not delivery:
            return error_response('Delivery not found for this order', status=404)
        
        # Count existing revision requests for this order
        revision_count = OrderRevisionRequest.query.filter_by(order_id=order_id).count() + 1
        
        # Create revision request
        revision_request = OrderRevisionRequest(
            order_id=order_id,
            delivery_id=delivery.id,
            requested_by=current_user_id,
            revision_notes=data['revision_notes'],
            revision_count=revision_count,
            status=RevisionRequestStatus.PENDING
        )
        
        # Update order status to REVISION
        order.status = OrderStatus.REVISION
        order.updated_at = datetime.now(timezone.utc)
        
        db.session.add(revision_request)
        db.session.commit()
        
        logger.info(
            f'Revision request {revision_request.id} created for order {order_id} '
            f'by user {current_user_id}'
        )
        
        # Send notifications
        try:
            # Notify client
            create_notification(
                user_id=current_user_id,
                title='Revision Request Submitted',
                message=f'Your revision request for order {order.order_number} has been submitted.',
                type=NotificationType.INFO,
                link=f'/orders/{order.id}'
            )
            
            # Notify admins
            admins = User.query.filter_by(is_admin=True, is_active=True).all()
            for admin in admins:
                create_notification(
                    user_id=admin.id,
                    title=f'New Revision Request - {order.order_number}',
                    message=f'{order.client.get_name()} requested revisions for "{order.title}"',
                    type=NotificationType.WARNING,
                    link=f'/admin/orders/{order.id}'
                )
        except Exception as e:
            logger.error(f'Notification error for revision request {revision_request.id}: {str(e)}')
        
        # Send email
        try:
            from tuned.services.email_service import send_revision_request_email_admin
            send_revision_request_email_admin(order, data['revision_notes'])
        except Exception as e:
            logger.error(f'Email error for revision request {revision_request.id}: {str(e)}')
        
        return created_response(
            data={'revision_request': revision_request.to_dict()},
            message='Revision request submitted successfully. Admin will review and make the necessary changes.'
        )
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error creating revision request for order {order_id}: {str(e)}', exc_info=True)
        return error_response('An error occurred while processing your revision request', status=500)


@client_bp.route('/orders/<int:order_id>/revision-requests', methods=['GET'])
@jwt_required()
@require_resource_ownership(Order, 'order_id', 'client_id')
def list_revision_requests(order_id):
    """
    List all revision requests for a specific order.
    
    Query Parameters:
        status: Filter by status (optional)
        
    Returns:
        200: List of revision requests
        404: Order not found
    """
    order = g.resource  # Pre-loaded by decorator
    
    # Build query
    query = OrderRevisionRequest.query.filter_by(order_id=order_id)
    
    # Filter by status if provided
    status_filter = request.args.get('status')
    if status_filter:
        try:
            status_enum = RevisionRequestStatus(status_filter)
            query = query.filter_by(status=status_enum)
        except ValueError:
            return error_response(f'Invalid status: {status_filter}', status=400)
    
    # Order by most recent first
    revision_requests = query.order_by(OrderRevisionRequest.requested_at.desc()).all()
    
    return success_response(
        data={
            'revision_requests': [rr.to_dict() for rr in revision_requests],
            'count': len(revision_requests)
        },
        message='Revision requests retrieved successfully'
    )


@client_bp.route('/orders/<int:order_id>/revision-requests/<int:request_id>', methods=['DELETE'])
@jwt_required()
@require_resource_ownership(Order, 'order_id', 'client_id')
@log_activity('revision_request_cancelled', 'OrderRevisionRequest')
def cancel_revision_request(order_id, request_id):
    """
    Cancel a pending revision request.
    
    Only pending requests can be cancelled by clients.
    
    Returns:
        200: Request cancelled successfully
        403: Cannot cancel request in current status
        404: Request not found
    """
    order = g.resource  # Pre-loaded by decorator
    current_user_id = int(get_jwt_identity())
    
    try:
        # Find revision request
        revision_request = OrderRevisionRequest.query.filter_by(
            id=request_id,
            order_id=order_id
        ).first()
        
        if not revision_request:
            return error_response('Revision request not found', status=404)
        
        # Only allow cancelling pending requests
        if revision_request.status != RevisionRequestStatus.PENDING:
            return error_response(
                f'Cannot cancel revision request with status: {revision_request.status.value}',
                status=403
            )
        
        # Update status to cancelled
        revision_request.status = RevisionRequestStatus.CANCELLED
        revision_request.resolved_at = datetime.now(timezone.utc)
        
        # If this was the only active revision request, revert order status
        active_revisions = OrderRevisionRequest.query.filter_by(
            order_id=order_id
        ).filter(
            OrderRevisionRequest.status.in_([
                RevisionRequestStatus.PENDING,
                RevisionRequestStatus.IN_PROGRESS
            ]),
            OrderRevisionRequest.id != request_id
        ).count()
        
        if active_revisions == 0:
            order.status = OrderStatus.COMPLETED
            order.updated_at = datetime.now(timezone.utc)
        
        db.session.commit()
        
        logger.info(f'Revision request {request_id} cancelled by user {current_user_id}')
        
        # Notify admins
        try:
            admins = User.query.filter_by(is_admin=True, is_active=True).all()
            for admin in admins:
                create_notification(
                    user_id=admin.id,
                    title=f'Revision Request Cancelled - {order.order_number}',
                    message=f'Client cancelled revision request for "{order.title}"',
                    type=NotificationType.INFO,
                    link=f'/admin/orders/{order.id}'
                )
        except Exception as e:
            logger.error(f'Notification error for cancelled revision {request_id}: {str(e)}')
        
        return success_response(
            data={'revision_request': revision_request.to_dict()},
            message='Revision request cancelled successfully'
        )
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error cancelling revision request {request_id}: {str(e)}', exc_info=True)
        return error_response('An error occurred while cancelling the revision request', status=500)


@client_bp.route('/orders/<int:order_id>/revision-requests/<int:request_id>', methods=['GET'])
@jwt_required()
@require_resource_ownership(Order, 'order_id', 'client_id')
def get_revision_request(order_id, request_id):
    """
    Get details of a specific revision request.
    
    Returns:
        200: Revision request details
        404: Request not found
    """
    order = g.resource  # Pre-loaded by decorator
    
    revision_request = OrderRevisionRequest.query.filter_by(
        id=request_id,
        order_id=order_id
    ).first()
    
    if not revision_request:
        return error_response('Revision request not found', status=404)
    
    return success_response(
        data={'revision_request': revision_request.to_dict()},
        message='Revision request retrieved successfully'
    )
