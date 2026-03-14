"""
Admin routes for creating deadline extension requests.

When admin needs more time to complete an order, they create an extension request
that the client can approve or reject.
"""
from flask import request, g
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError
from datetime import datetime, timezone
import logging

from tuned.admin import admin_bp
from tuned.client.schemas import CreateDeadlineExtensionRequestSchema, DeadlineExtensionFilterSchema
from tuned.models.deadline_extension import OrderDeadlineExtensionRequest
from tuned.models.order import Order
from tuned.models.user import User
from tuned.models.enums import OrderStatus, ExtensionRequestStatus
from tuned.extensions import db
from tuned.utils import (
    success_response,
    error_response,
    validation_error_response,
    created_response
)
from tuned.utils.decorators import require_admin, log_activity
from tuned.services.notification_service import create_notification
from tuned.models.enums import NotificationType

logger = logging.getLogger(__name__)


@admin_bp.route('/orders/<int:order_id>/deadline-extension-requests', methods=['POST'])
@jwt_required()
@require_admin()
@log_activity('deadline_extension_requested', 'OrderDeadlineExtensionRequest')
def create_extension_request(order_id):
    """
    Create a deadline extension request for an order (admin only).
    
    When admin needs more time to complete the work, they request an extension
    from the client with a reason and requested hours.
    
    Request Body:
        {
            "requested_hours": int (required, 12-720),
            "reason": str (required, 20-1000 chars)
        }
    
    Returns:
        201: Extension request created successfully
        400: Validation error
        403: Order not eligible for extension
        404: Order not found
    """
    current_user_id = int(get_jwt_identity())
    
    # Validate request data
    schema = CreateDeadlineExtensionRequestSchema()
    try:
        data = schema.load(request.get_json())
    except ValidationError as e:
        return validation_error_response(e.messages)
    
    try:
        # Verify order exists
        order = Order.query.filter_by(
            id=order_id,
            is_deleted=False
        ).first()
        
        if not order:
            return error_response('Order not found', status=404)
        
        # Verify order is eligible for deadline extension
        if order.status not in [OrderStatus.PENDING, OrderStatus.ACTIVE, OrderStatus.OVERDUE]:
            return error_response(
                f'Cannot request deadline extension for orders with status: {order.status.value}',
                status=403
            )
        
        if not order.paid:
            return error_response('Cannot request deadline extension for unpaid orders', status=403)
        
        # Check if there's already a pending extension request
        pending_request = OrderDeadlineExtensionRequest.query.filter_by(
            order_id=order_id,
            status=ExtensionRequestStatus.PENDING
        ).first()
        
        if pending_request:
            return error_response(
                'There is already a pending deadline extension request for this order',
                status=403
            )
        
        # Create deadline extension request
        extension_request = OrderDeadlineExtensionRequest(
            order_id=order_id,
            requested_by=current_user_id,  # Admin is the requester
            requested_hours=data['requested_hours'],
            reason=data['reason'],
            original_due_date=order.due_date,
            status=ExtensionRequestStatus.PENDING
        )
        
        # Mark order as having extension requested
        order.extension_requested = True
        order.extension_requested_at = datetime.now(timezone.utc)
        order.updated_at = datetime.now(timezone.utc)
        
        db.session.add(extension_request)
        db.session.commit()
        
        logger.info(
            f'Deadline extension request {extension_request.id} created for order {order_id} '
            f'by admin {current_user_id} ({data["requested_hours"]} hours)'
        )
        
        # Send notifications
        try:
            # Notify client (they need to approve/reject)
            create_notification(
                user_id=order.client_id,
                title=f'Extension Request - {order.order_number}',
                message=f'Admin has requested a {data["requested_hours"]} hour extension for your order. Please review.',
                type=NotificationType.WARNING,
                link=f'/orders/{order.id}'
            )
            
            # Notify admin (confirmation)
            create_notification(
                user_id=current_user_id,
                title=f'Extension Request Submitted - {order.order_number}',
                message=f'Your extension request has been sent to the client for approval.',
                type=NotificationType.INFO,
                link=f'/admin/orders/{order.id}'
            )
        except Exception as e:
            logger.error(f'Notification error for extension request {extension_request.id}: {str(e)}')
        
        # Send email to client
        try:
            from tuned.services.email_service import send_deadline_extension_request_email_client
            send_deadline_extension_request_email_client(order, data['requested_hours'], data['reason'])
        except Exception as e:
            logger.error(f'Email error for extension request {extension_request.id}: {str(e)}')
        
        return created_response(
            data={'extension_request': extension_request.to_dict()},
            message='Deadline extension request submitted to client for approval.'
        )
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error creating deadline extension request for order {order_id}: {str(e)}', exc_info=True)
        return error_response('An error occurred while processing the extension request', status=500)


@admin_bp.route('/deadline-extension-requests', methods=['GET'])
@jwt_required()
@require_admin()
def list_all_extension_requests():
    """
    List all deadline extension requests across all orders (admin only).
    
    Query Parameters:
        status: Filter by status (pending, approved, rejected, cancelled)
        order_id: Filter by specific order ID
        page: Page number (default: 1)
        per_page: Items per page (default: 20, max: 100)
        
    Returns:
        200: Paginated list of extension requests
    """
    schema = DeadlineExtensionFilterSchema()
    try:
        filters = schema.load(request.args)
    except ValidationError as e:
        return validation_error_response(e.messages)
    
    query = OrderDeadlineExtensionRequest.query
    
    if filters.get('status'):
        status_enum = ExtensionRequestStatus(filters['status'])
        query = query.filter_by(status=status_enum)
    
    order_id = request.args.get('order_id', type=int)
    if order_id:
        query = query.filter_by(order_id=order_id)
    
    query = query.order_by(OrderDeadlineExtensionRequest.requested_at.desc())
    
    page = filters.get('page', 1)
    per_page = filters.get('per_page', 20)
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    extension_requests = [er.to_dict(include_client_notes=True) for er in pagination.items]
    
    return success_response(
        data={
            'extension_requests': extension_requests,
            'pagination': {
                'page': pagination.page,
                'per_page': pagination.per_page,
                'total_pages': pagination.pages,
                'total_items': pagination.total,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            },
            'stats': {
                'pending': OrderDeadlineExtensionRequest.query.filter_by(status=ExtensionRequestStatus.PENDING).count(),
                'approved': OrderDeadlineExtensionRequest.query.filter_by(status=ExtensionRequestStatus.APPROVED).count(),
                'rejected': OrderDeadlineExtensionRequest.query.filter_by(status=ExtensionRequestStatus.REJECTED).count(),
            }
        },
        message='Extension requests retrieved successfully'
    )


@admin_bp.route('/deadline-extension-requests/<int:request_id>', methods=['DELETE'])
@jwt_required()
@require_admin()
@log_activity('deadline_extension_cancelled', 'OrderDeadlineExtensionRequest')
def cancel_extension_request(request_id):
    """
    Cancel a pending deadline extension request (admin only).
    
    Admin can cancel their own extension request before client responds.
    
    Returns:
        200: Request cancelled successfully
        403: Cannot cancel request in current status
        404: Request not found
    """
    current_user_id = int(get_jwt_identity())
    
    try:
        extension_request = OrderDeadlineExtensionRequest.query.get(request_id)
        
        if not extension_request:
            return error_response('Extension request not found', status=404)
        
        if extension_request.status != ExtensionRequestStatus.PENDING:
            return error_response(
                f'Cannot cancel extension request with status: {extension_request.status.value}',
                status=403
            )
        
        extension_request.status = ExtensionRequestStatus.CANCELLED
        extension_request.reviewed_at = datetime.now(timezone.utc)
        
        order = extension_request.order
        order.extension_requested = False
        order.updated_at = datetime.now(timezone.utc)
        
        db.session.commit()
        
        logger.info(f'Extension request {request_id} cancelled by admin {current_user_id}')
        
        # Notify client
        try:
            create_notification(
                user_id=order.client_id,
                title=f'Extension Request Cancelled - {order.order_number}',
                message='The deadline extension request has been cancelled by admin.',
                type=NotificationType.INFO,
                link=f'/orders/{order.id}'
            )
        except Exception as e:
            logger.error(f'Notification error: {str(e)}')
        
        return success_response(
            data={'extension_request': extension_request.to_dict()},
            message='Extension request cancelled successfully'
        )
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error cancelling extension request {request_id}: {str(e)}', exc_info=True)
        return error_response('An error occurred while cancelling the request', status=500)
