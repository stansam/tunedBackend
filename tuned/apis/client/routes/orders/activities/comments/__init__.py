"""
Order comments route for client blueprint.

Handles adding, updating, and retrieving comments on orders.
"""

from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError
from datetime import datetime, timezone
import logging

from tuned.client import client_bp
from tuned.client.schemas import OrderCommentSchema, UpdateOrderCommentSchema
from tuned.models.order import Order, OrderComment
from tuned.models.user import User
from tuned.extensions import db
from tuned.utils import success_response, error_response, validation_error_response, created_response
from tuned.utils.decorators import rate_limit, log_activity
from tuned.services.notification_service import create_notification
from tuned.models.enums import NotificationType

logger = logging.getLogger(__name__)


@client_bp.route('/orders/<int:order_id>/comments', methods=['POST'])
@jwt_required()
@rate_limit(max_requests=50, window=3600)  # 50 comments per hour
@log_activity('comment_added', 'OrderComment')
def add_order_comment(order_id):
    """
    Add a comment to an order.
    
    Args:
        order_id: ID of the order
        
    Request Body:
        {
            "message": str (1-5000 chars)
        }
    
    Returns:
        201: Comment added successfully
        404: Order not found
        403: Unauthorized access
        400: Validation error
    """
    current_user_id = get_jwt_identity()
    
    # Validate input
    schema = OrderCommentSchema()
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
        
        # Create comment
        comment = OrderComment(
            order_id=order.id,
            user_id=current_user_id,
            message=data['message'],
            created_at=datetime.now(timezone.utc)
        )
        
        db.session.add(comment)
        db.session.commit()
        
        logger.info(f'Comment added to order {order_id} by user {current_user_id}')
        
        # Notify admins about new comment
        try:
            admins = User.query.filter_by(is_admin=True, is_active=True).all()
            for admin in admins:
                create_notification(
                    user_id=admin.id,
                    title=f'New Comment on Order {order.order_number}',
                    message=f'{order.client.get_name()} commented on "{order.title}"',
                    type=NotificationType.INFO,
                    link=f'/admin/orders/{order.id}'
                )
        except Exception as e:
            logger.error(f'Notification error for comment on order {order_id}: {str(e)}')
        
        # Prepare response
        comment_data = {
            'id': comment.id,
            'order_id': comment.order_id,
            'message': comment.message,
            'user': {
                'id': current_user_id,
                'name': comment.user.get_name()
            },
            'created_at': comment.created_at.isoformat()
        }
        
        return created_response(
            data={'comment': comment_data},
            message='Comment added successfully'
        )
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error adding comment to order {order_id}: {str(e)}', exc_info=True)
        return error_response('An error occurred while adding the comment', status=500)


@client_bp.route('/orders/<int:order_id>/comments', methods=['GET'])
@jwt_required()
@rate_limit(max_requests=100, window=60)
def get_order_comments(order_id):
    """
    Get all comments for an order.
    
    Args:
        order_id: ID of the order
    
    Returns:
        200: List of comments
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
        
        # Get all comments
        comments = OrderComment.query.filter_by(
            order_id=order_id,
            is_deleted=False
        ).order_by(OrderComment.created_at.desc()).all()
        
        # Serialize comments
        comments_data = []
        for comment in comments:
            comments_data.append({
                'id': comment.id,
                'message': comment.message,
                'user': {
                    'id': comment.user_id,
                    'name': comment.user.get_name(),
                    'is_admin': comment.user.is_admin
                },
                'created_at': comment.created_at.isoformat(),
                'updated_at': comment.updated_at.isoformat() if comment.updated_at else None
            })
        
        logger.info(f'Retrieved {len(comments_data)} comments for order {order_id}')
        
        return success_response(
            data={'comments': comments_data},
            message=f'Retrieved {len(comments_data)} comments'
        )
        
    except Exception as e:
        logger.error(f'Error retrieving comments for order {order_id}: {str(e)}', exc_info=True)
        return error_response('An error occurred while retrieving comments', status=500)


@client_bp.route('/orders/<int:order_id>/comments/<int:comment_id>', methods=['PUT'])
@jwt_required()
@rate_limit(max_requests=30, window=3600)
@log_activity('comment_updated', 'OrderComment')
def update_order_comment(order_id, comment_id):
    """
    Update a comment on an order.
    
    Args:
        order_id: ID of the order
        comment_id: ID of the comment
        
    Request Body:
        {
            "message": str (1-5000 chars)
        }
    
    Returns:
        200: Comment updated successfully
        404: Order or comment not found
        403: Unauthorized access
        400: Validation error
    """
    current_user_id = get_jwt_identity()
    
    # Validate input
    schema = UpdateOrderCommentSchema()
    try:
        data = schema.load(request.get_json())
    except ValidationError as e:
        return validation_error_response(e.messages)
    
    try:
        # Verify comment exists and user owns it
        comment = OrderComment.query.filter_by(
            id=comment_id,
            order_id=order_id,
            user_id=current_user_id,
            is_deleted=False
        ).first()
        
        if not comment:
            return error_response('Comment not found or unauthorized', status=404)
        
        # Update comment
        comment.message = data['message']
        comment.updated_at = datetime.now(timezone.utc)
        
        db.session.commit()
        
        logger.info(f'Comment {comment_id} updated on order {order_id} by user {current_user_id}')
        
        # Prepare response
        comment_data = {
            'id': comment.id,
            'message': comment.message,
            'created_at': comment.created_at.isoformat(),
            'updated_at': comment.updated_at.isoformat()
        }
        
        return success_response(
            data={'comment': comment_data},
            message='Comment updated successfully'
        )
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error updating comment {comment_id}: {str(e)}', exc_info=True)
        return error_response('An error occurred while updating the comment', status=500)


@client_bp.route('/orders/<int:order_id>/comments/<int:comment_id>', methods=['DELETE'])
@jwt_required()
@rate_limit(max_requests=30, window=3600)
@log_activity('comment_deleted', 'OrderComment')
def delete_order_comment(order_id, comment_id):
    """
    Delete a comment from an order (soft delete).
    
    Args:
        order_id: ID of the order
        comment_id: ID of the comment
    
    Returns:
        200: Comment deleted successfully
        404: Comment not found
        403: Unauthorized access
    """
    current_user_id = get_jwt_identity()
    
    try:
        # Verify comment exists and user owns it
        comment = OrderComment.query.filter_by(
            id=comment_id,
            order_id=order_id,
            user_id=current_user_id,
            is_deleted=False
        ).first()
        
        if not comment:
            return error_response('Comment not found or unauthorized', status=404)
        
        # Soft delete
        comment.is_deleted = True
        comment.deleted_at = datetime.now(timezone.utc)
        
        db.session.commit()
        
        logger.info(f'Comment {comment_id} deleted from order {order_id} by user {current_user_id}')
        
        return success_response(
            message='Comment deleted successfully'
        )
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error deleting comment {comment_id}: {str(e)}', exc_info=True)
        return error_response('An error occurred while deleting the comment', status=500)
