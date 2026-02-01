"""
Client routes for reviewing deadline extension requests.

Clients can view and approve/reject deadline extension requests submitted by admin.
"""
from flask import request, g
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError
from datetime import datetime, timezone, timedelta
import logging

from tuned.client import client_bp
from tuned.client.schemas import UpdateDeadlineExtensionRequestSchema
from tuned.models.order import Order
from tuned.models.deadline_extension import OrderDeadlineExtensionRequest
from tuned.models.user import User
from tuned.models.enums import ExtensionRequestStatus
from tuned.extensions import db
from tuned.utils import (
    success_response,
    error_response,
    validation_error_response
)
from tuned.utils.decorators import log_activity, require_resource_ownership
from tuned.services.notification_service import create_notification
from tuned.models.enums import NotificationType

logger = logging.getLogger(__name__)


@client_bp.route('/orders/<int:order_id>/deadline-extension-requests', methods=['GET'])
@jwt_required()
@require_resource_ownership(Order, 'order_id', 'client_id')
def list_deadline_extension_requests(order_id):
    """
    List all deadline extension requests for a specific order.
    
    Shows extension requests made by admin that client can approve/reject.
    
    Query Parameters:
        status: Filter by status (optional)
        
    Returns:
        200: List of deadline extension requests
        404: Order not found
    """
    order = g.resource  # Pre-loaded by decorator
    
    query = OrderDeadlineExtensionRequest.query.filter_by(order_id=order_id)
    
    # Filter by status if provided
    status_filter = request.args.get('status')
    if status_filter:
        try:
            status_enum = ExtensionRequestStatus(status_filter)
            query = query.filter_by(status=status_enum)
        except ValueError:
            return error_response(f'Invalid status: {status_filter}', status=400)
    
    extension_requests = query.order_by(OrderDeadlineExtensionRequest.requested_at.desc()).all()
    
    return success_response(
        data={
            'extension_requests': [er.to_dict() for er in extension_requests],
            'count': len(extension_requests)
        },
        message='Deadline extension requests retrieved successfully'
    )


@client_bp.route('/orders/<int:order_id>/deadline-extension-requests/<int:request_id>', methods=['GET'])
@jwt_required()
@require_resource_ownership(Order, 'order_id', 'client_id')
def get_deadline_extension_request(order_id, request_id):
    """
    Get details of a specific deadline extension request.
    
    Returns:
        200: Extension request details
        404: Request not found
    """
    order = g.resource
    
    extension_request = OrderDeadlineExtensionRequest.query.filter_by(
        id=request_id,
        order_id=order_id
    ).first()
    
    if not extension_request:
        return error_response('Deadline extension request not found', status=404)
    
    return success_response(
        data={'extension_request': extension_request.to_dict()},
        message='Deadline extension request retrieved successfully'
    )


@client_bp.route('/orders/<int:order_id>/deadline-extension-requests/<int:request_id>/approve', methods=['POST'])
@jwt_required()
@require_resource_ownership(Order, 'order_id', 'client_id')
@log_activity('deadline_extension_approved', 'OrderDeadlineExtensionRequest')
def approve_extension_request(order_id, request_id):
    """
    Approve a deadline extension request from admin.
    
    Client approves the requested extension, and the order deadline is updated.
    
    Request Body:
        {
            "client_notes": str (optional) - Client's notes about the approval
            "approved_hours": int (optional) - Can approve different hours than requested
        }
    
    Returns:
        200: Request approved successfully
        403: Cannot approve request in current status
        404: Request not found
    """
    order = g.resource
    current_user_id = int(get_jwt_identity())
    
    try:
        data = request.get_json() or {}
        
        extension_request = OrderDeadlineExtensionRequest.query.filter_by(
            id=request_id,
            order_id=order_id
        ).first()
        
        if not extension_request:
            return error_response('Extension request not found', status=404)
        
        if extension_request.status != ExtensionRequestStatus.PENDING:
            return error_response(
                f'Cannot approve extension request with status: {extension_request.status.value}',
                status=403
            )
        
        # Use approved_hours if provided, otherwise use requested_hours
        approved_hours = data.get('approved_hours', extension_request.requested_hours)
        
        # Validate approved hours
        if approved_hours < 1 or approved_hours > 720:
            return error_response('Approved hours must be between 1 and 720', status=400)
        
        # Calculate new due date
        new_due_date = extension_request.original_due_date + timedelta(hours=approved_hours)
        
        # Update extension request
        extension_request.status = ExtensionRequestStatus.APPROVED
        extension_request.new_due_date = new_due_date
        extension_request.reviewed_at = datetime.now(timezone.utc)
        extension_request.reviewed_by = current_user_id
        
        if 'client_notes' in data:
            extension_request.client_notes = data['client_notes']
        
        # Update order due date
        order.due_date = new_due_date
        order.extension_requested = False
        order.updated_at = datetime.now(timezone.utc)
        
        db.session.commit()
        
        logger.info(
            f'Extension request {request_id} approved by client {current_user_id}. '
            f'Order {order_id} deadline extended to {new_due_date}'
        )
        
        # Send notifications
        try:
            # Notify admin
            admin_user = extension_request.requester
            create_notification(
                user_id=admin_user.id,
                title=f'Extension Approved - {order.order_number}',
                message=f'Client approved your {approved_hours} hour extension request. New deadline: {new_due_date.strftime("%Y-%m-%d %H:%M")}',
                type=NotificationType.SUCCESS,
                link=f'/admin/orders/{order.id}'
            )
            
            # Confirm to client
            create_notification(
                user_id=current_user_id,
                title=f'Extension Approved - {order.order_number}',
                message=f'You approved the extension request. New deadline: {new_due_date.strftime("%Y-%m-%d %H:%M")}',
                type=NotificationType.SUCCESS,
                link=f'/orders/{order.id}'
            )
        except Exception as e:
            logger.error(f'Notification error: {str(e)}')
        
        return success_response(
            data={'extension_request': extension_request.to_dict(include_client_notes=True)},
            message=f'Extension request approved. Deadline extended by {approved_hours} hours.'
        )
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error approving extension request {request_id}: {str(e)}', exc_info=True)
        return error_response('An error occurred while approving the request', status=500)


@client_bp.route('/orders/<int:order_id>/deadline-extension-requests/<int:request_id>/reject', methods=['POST'])
@jwt_required()
@require_resource_ownership(Order, 'order_id', 'client_id')
@log_activity('deadline_extension_rejected', 'OrderDeadlineExtensionRequest')
def reject_extension_request(order_id, request_id):
    """
    Reject a deadline extension request from admin.
    
    Client rejects the extension request with a reason.
    
    Request Body:
        {
            "rejection_reason": str (required) - Reason for rejection
            "client_notes": str (optional) - Additional notes
        }
    
    Returns:
        200: Request rejected successfully
        400: Missing rejection reason
        403: Cannot reject request in current status
        404: Request not found
    """
    order = g.resource
    current_user_id = int(get_jwt_identity())
    
    try:
        data = request.get_json() or {}
        
        if 'rejection_reason' not in data or not data['rejection_reason']:
            return error_response('Rejection reason is required', status=400)
        
        extension_request = OrderDeadlineExtensionRequest.query.filter_by(
            id=request_id,
            order_id=order_id
        ).first()
        
        if not extension_request:
            return error_response('Extension request not found', status=404)
        
        if extension_request.status != ExtensionRequestStatus.PENDING:
            return error_response(
                f'Cannot reject extension request with status: {extension_request.status.value}',
                status=403
            )
        
        # Update extension request
        extension_request.status = ExtensionRequestStatus.REJECTED
        extension_request.rejection_reason = data['rejection_reason']
        extension_request.reviewed_at = datetime.now(timezone.utc)
        extension_request.reviewed_by = current_user_id
        
        if 'client_notes' in data:
            extension_request.client_notes = data['client_notes']
        
        # Update order flags
        order.extension_requested = False
        order.updated_at = datetime.now(timezone.utc)
        
        db.session.commit()
        
        logger.info(f'Extension request {request_id} rejected by client {current_user_id}')
        
        # Send notifications
        try:
            # Notify admin
            admin_user = extension_request.requester
            create_notification(
                user_id=admin_user.id,
                title=f'Extension Rejected - {order.order_number}',
                message=f'Client rejected your extension request. Reason: {data["rejection_reason"]}',
                type=NotificationType.WARNING,
                link=f'/admin/orders/{order.id}'
            )
            
            # Confirm to client
            create_notification(
                user_id=current_user_id,
                title=f'Extension Rejected - {order.order_number}',
                message='You rejected the extension request.',
                type=NotificationType.INFO,
                link=f'/orders/{order.id}'
            )
        except Exception as e:
            logger.error(f'Notification error: {str(e)}')
        
        return success_response(
            data={'extension_request': extension_request.to_dict(include_client_notes=True)},
            message='Extension request rejected successfully'
        )
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error rejecting extension request {request_id}: {str(e)}', exc_info=True)
        return error_response('An error occurred while rejecting the request', status=500)
