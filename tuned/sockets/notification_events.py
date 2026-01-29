"""
Socket.IO notification events.

Handles real-time notification delivery via WebSocket.
"""
from flask import request
from flask_socketio import emit, join_room, leave_room
from flask_jwt_extended import decode_token, get_jwt_identity
from tuned.extensions import socketio
from tuned.services.notification_service import mark_notification_as_read, get_unread_count
import logging


logger = logging.getLogger(__name__)


@socketio.on('connect')
def handle_connect():
    """
    Handle client connection.
    
    Authenticate user and join their personal notification room.
    """
    try:
        # Get JWT token from query params or auth header
        auth_token = request.args.get('token')
        
        if not auth_token:
            logger.warning("WebSocket connection attempt without token")
            return False
        
        # Decode token to get user ID
        try:
            token_data = decode_token(auth_token)
            user_id = token_data['sub']  # 'sub' is the identity claim
        except Exception as e:
            logger.warning(f"Invalid WebSocket auth token: {str(e)}")
            return False
        
        # Join user's personal room
        room = f'user_{user_id}'
        join_room(room)
        
        logger.info(f"User {user_id} connected to WebSocket, joined room: {room}")
        
        # Send initial unread count
        emit('notification:count', {'unread_count': get_unread_count(user_id)})
        
        return True
        
    except Exception as e:
        logger.error(f"WebSocket connection error: {str(e)}")
        return False


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    logger.debug("Client disconnected from WebSocket")


@socketio.on('notification:mark_read')
def handle_mark_notification_read(data):
    """
    Mark a notification as read.
    
    Args:
        data: {'notification_id': int}
    """
    try:
        notification_id = data.get('notification_id')
        
        if not notification_id:
            emit('error', {'message': 'Notification ID is required'})
            return
        
        # Mark as read
        success = mark_notification_as_read(notification_id)
        
        if success:
            emit('notification:read', {'notification_id': notification_id})
            logger.debug(f"Notification {notification_id} marked as read via WebSocket")
        else:
            emit('error', {'message': 'Notification not found'})
            
    except Exception as e:
        logger.error(f"Error marking notification as read: {str(e)}")
        emit('error', {'message': 'An error occurred'})


@socketio.on('notification:get_unread_count')
def handle_get_unread_count():
    """
    Get unread notification count for current user.
    
    Returns count via 'notification:count' event.
    """
    try:
        # Get user from JWT (assuming authenticated connection)
        # In production, you'd extract user_id from the socket session
        # For now, this is a placeholder
        emit('notification:count', {'unread_count': 0})
        
    except Exception as e:
        logger.error(f"Error getting unread count: {str(e)}")
        emit('error', {'message': 'An error occurred'})
