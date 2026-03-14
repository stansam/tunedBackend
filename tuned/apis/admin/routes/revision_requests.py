"""
Admin routes for revision request management.

Handles admin operations for reviewing, updating, and managing revision requests.
"""
from flask import request, g
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError
from datetime import datetime, timezone
import logging

from tuned.admin import admin_bp
from tuned.client.schemas import UpdateRevisionRequestSchema, RevisionRequestFilterSchema
from tuned.models.revision_request import OrderRevisionRequest
from tuned.models.order import Order
from tuned.models.user import User
from tuned.models.enums import RevisionRequestStatus, OrderStatus, Priority
from tuned.extensions import db
from tuned.utils import (
    success_response,
    error_response,
    validation_error_response
)
from tuned.utils.decorators import require_admin, log_activity
from tuned.services.notification_service import create_notification
from tuned.models.enums import NotificationType

logger = logging.getLogger(__name__)


@admin_bp.route('/revision-requests', methods=['GET'])
@jwt_required()
@require_admin()
def list_all_revision_requests():
    """
    List all revision requests across all orders (admin only).
    
    Supports filtering and pagination for efficient management.
    
    Query Parameters:
        status: Filter by status (pending, in_progress, completed, rejected, cancelled)
        priority: Filter by priority (low, normal, high, urgent)
        order_id: Filter by specific order ID
        page: Page number (default: 1)
        per_page: Items per page (default: 20, max: 100)
        sort_by: Sort field (requested_at, status, priority)
        sort_order: Sort direction (asc, desc)
        
    Returns:
        200: Paginated list of revision requests with metadata
    """
    # Validate query parameters
    schema = RevisionRequestFilterSchema()
    try:
        filters = schema.load(request.args)
    except ValidationError as e:
        return validation_error_response(e.messages)
    
    # Build query
    query = OrderRevisionRequest.query
    
    # Apply filters
    if filters.get('status'):
        status_enum = RevisionRequestStatus(filters['status'])
        query = query.filter_by(status=status_enum)
    
    if filters.get('priority'):
        priority_enum = Priority(filters['priority'])
        query = query.filter_by(priority=priority_enum)
    
    order_id = request.args.get('order_id', type=int)
    if order_id:
        query = query.filter_by(order_id=order_id)
    
    # Sorting
    sort_by = request.args.get('sort_by', 'requested_at')
    sort_order = request.args.get('sort_order', 'desc')
    
    if sort_by == 'requested_at':
        order_clause = OrderRevisionRequest.requested_at.desc() if sort_order == 'desc' else OrderRevisionRequest.requested_at.asc()
    elif sort_by == 'status':
        order_clause = OrderRevisionRequest.status.desc() if sort_order == 'desc' else OrderRevisionRequest.status.asc()
    elif sort_by == 'priority':
        order_clause = OrderRevisionRequest.priority.desc() if sort_order == 'desc' else OrderRevisionRequest.priority.asc()
    else:
        order_clause = OrderRevisionRequest.requested_at.desc()
    
    query = query.order_by(order_clause)
    
    # Pagination
    page = filters.get('page', 1)
    per_page = filters.get('per_page', 20)
    
    pagination = query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    
    # Prepare response
    revision_requests = [rr.to_dict(include_internal=True) for rr in pagination.items]
    
    return success_response(
        data={
            'revision_requests': revision_requests,
            'pagination': {
                'page': pagination.page,
                'per_page': pagination.per_page,
                'total_pages': pagination.pages,
                'total_items': pagination.total,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            },
            'stats': {
                'pending': OrderRevisionRequest.query.filter_by(status=RevisionRequestStatus.PENDING).count(),
                'in_progress': OrderRevisionRequest.query.filter_by(status=RevisionRequestStatus.IN_PROGRESS).count(),
                'completed': OrderRevisionRequest.query.filter_by(status=RevisionRequestStatus.COMPLETED).count(),
            }
        },
        message='Revision requests retrieved successfully'
    )


@admin_bp.route('/revision-requests/<int:request_id>', methods=['GET'])
@jwt_required()
@require_admin()
def get_revision_request_details(request_id):
    """
    Get detailed information about a specific revision request (admin only).
    
    Returns:
        200: Detailed revision request information
        404: Request not found
    """
    revision_request = OrderRevisionRequest.query.get(request_id)
    
    if not revision_request:
        return error_response('Revision request not found', status=404)
    
    return success_response(
        data={'revision_request': revision_request.to_dict(include_internal=True)},
        message='Revision request retrieved successfully'
    )


@admin_bp.route('/revision-requests/<int:request_id>', methods=['PATCH'])
@jwt_required()
@require_admin()
@log_activity('revision_request_updated', 'OrderRevisionRequest')
def update_revision_request(request_id):
    """
    Update a revision request (admin only).
    
    Admins can update status, priority, internal notes, and estimated completion.
    
    Request Body:
        {
            "status": str (optional) - pending, in_progress, completed, rejected, cancelled
            "priority": str (optional) - low, normal, high, urgent
            "internal_notes": str (optional) - Admin-only notes
            "estimated_completion": str (optional) - ISO datetime
        }
    
    Returns:
        200: Request updated successfully
        400: Validation error
        404: Request not found
    """
    current_user_id = int(get_jwt_identity())
    
    # Validate request data
    schema = UpdateRevisionRequestSchema()
    try:
        data = schema.load(request.get_json())
    except ValidationError as e:
        return validation_error_response(e.messages)
    
    try:
        # Find revision request
        revision_request = OrderRevisionRequest.query.get(request_id)
        
        if not revision_request:
            return error_response('Revision request not found', status=404)
        
        # Track changes for notifications
        status_changed = False
        old_status = revision_request.status
        
        # Update fields
        if 'status' in data:
            new_status = RevisionRequestStatus(data['status'])
            revision_request.status = new_status
            status_changed = True
            
            # Update timestamps based on status
            if new_status == RevisionRequestStatus.IN_PROGRESS and not revision_request.reviewed_at:
                revision_request.reviewed_at = datetime.now(timezone.utc)
                revision_request.reviewed_by = current_user_id
            
            if new_status in [RevisionRequestStatus.COMPLETED, RevisionRequestStatus.REJECTED]:
                revision_request.resolved_at = datetime.now(timezone.utc)
                if not revision_request.reviewed_by:
                    revision_request.reviewed_by = current_user_id
                
                # Update order status
                order = revision_request.order
                if new_status == RevisionRequestStatus.COMPLETED:
                    order.status = OrderStatus.COMPLETED
                    order.updated_at = datetime.now(timezone.utc)
        
        if 'priority' in data:
            revision_request.priority = Priority(data['priority'])
        
        if 'internal_notes' in data:
            revision_request.internal_notes = data['internal_notes']
        
        if 'estimated_completion' in data:
            revision_request.estimated_completion = data['estimated_completion']
        
        db.session.commit()
        
        logger.info(f'Revision request {request_id} updated by admin {current_user_id}')
        
        # Send notifications if status changed
        if status_changed:
            try:
                # Notify client
                client = revision_request.requester
                status_messages = {
                    RevisionRequestStatus.IN_PROGRESS: 'is now being processed',
                    RevisionRequestStatus.COMPLETED: 'has been completed',
                    RevisionRequestStatus.REJECTED: 'has been rejected',
                }
                
                if new_status in status_messages:
                    create_notification(
                        user_id=client.id,
                        title=f'Revision Request Update - {revision_request.order.order_number}',
                        message=f'Your revision request {status_messages[new_status]}.',
                        type=NotificationType.INFO if new_status == RevisionRequestStatus.COMPLETED else NotificationType.WARNING,
                        link=f'/orders/{revision_request.order_id}'
                    )
            except Exception as e:
                logger.error(f'Notification error for revision update {request_id}: {str(e)}')
        
        return success_response(
            data={'revision_request': revision_request.to_dict(include_internal=True)},
            message='Revision request updated successfully'
        )
        
    except ValueError as e:
        db.session.rollback()
        logger.error(f'Invalid status transition for revision {request_id}: {str(e)}')
        return error_response(str(e), status=400)
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error updating revision request {request_id}: {str(e)}', exc_info=True)
        return error_response('An error occurred while updating the revision request', status=500)


@admin_bp.route('/orders/<int:order_id>/revision-requests', methods=['GET'])
@jwt_required()
@require_admin()
def get_order_revision_requests(order_id):
    """
    Get all revision requests for a specific order (admin only).
    
    Returns:
        200: List of revision requests for the order
        404: Order not found
    """
    # Verify order exists
    order = Order.query.get(order_id)
    if not order:
        return error_response('Order not found', status=404)
    
    # Get all revision requests for this order
    revision_requests = OrderRevisionRequest.query.filter_by(
        order_id=order_id
    ).order_by(OrderRevisionRequest.requested_at.desc()).all()
    
    return success_response(
        data={
            'revision_requests': [rr.to_dict(include_internal=True) for rr in revision_requests],
            'count': len(revision_requests),
            'order': {
                'id': order.id,
                'order_number': order.order_number,
                'title': order.title,
                'status': order.status.value
            }
        },
        message='Revision requests retrieved successfully'
    )


@admin_bp.route('/revision-requests/stats', methods=['GET'])
@jwt_required()
@require_admin()
def get_revision_request_stats():
    """
    Get statistics and metrics for revision requests (admin only).
    
    Provides insights for dashboard and reporting.
    
    Returns:
        200: Statistics and metrics
    """
    from sqlalchemy import func
    from datetime import timedelta
    
    now = datetime.now(timezone.utc)
    last_30_days = now - timedelta(days=30)
    
    # Status counts
    status_counts = {}
    for status in RevisionRequestStatus:
        status_counts[status.value] = OrderRevisionRequest.query.filter_by(status=status).count()
    
    # Priority counts
    priority_counts = {}
    for priority in Priority:
        priority_counts[priority.value] = OrderRevisionRequest.query.filter_by(priority=priority).count()
    
    # Recent activity
    recent_requests = OrderRevisionRequest.query.filter(
        OrderRevisionRequest.requested_at >= last_30_days
    ).count()
    
    # Average resolution time for completed requests
    completed_requests = OrderRevisionRequest.query.filter(
        OrderRevisionRequest.status == RevisionRequestStatus.COMPLETED,
        OrderRevisionRequest.requested_at.isnot(None),
        OrderRevisionRequest.resolved_at.isnot(None)
    ).all()
    
    avg_resolution_hours = None
    if completed_requests:
        total_hours = sum([
            (rr.resolved_at - rr.requested_at).total_seconds() / 3600
            for rr in completed_requests
        ])
        avg_resolution_hours = round(total_hours / len(completed_requests), 2)
    
    return success_response(
        data={
            'status_counts': status_counts,
            'priority_counts': priority_counts,
            'recent_activity': {
                'last_30_days': recent_requests,
                'pending': status_counts.get('pending', 0),
                'in_progress': status_counts.get('in_progress', 0)
            },
            'metrics': {
                'total_requests': OrderRevisionRequest.query.count(),
                'avg_resolution_hours': avg_resolution_hours,
                'completion_rate': round(
                    (status_counts.get('completed', 0) / 
                     max(OrderRevisionRequest.query.count(), 1)) * 100, 2
                )
            }
        },
        message='Statistics retrieved successfully'
    )
