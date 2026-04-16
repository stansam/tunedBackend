from flask import request
from flask_socketio import emit, join_room, leave_room
from flask_login import current_user
from tuned.extensions import socketio
from tuned.interface import notification as notification_interface
import logging


logger = logging.getLogger(__name__)


@socketio.on('connect')
def handle_connect():
    try:
        if not current_user.is_authenticated:
            logger.warning("WebSocket connection attempt without authentication")
            return False
            
        user_id = current_user.id
        room = f'user_{user_id}'
        join_room(room)
        
        logger.info(f"User {user_id} connected to WebSocket, joined room: {room}")
        
        unread = notification_interface.get_unread_count(str(user_id))
        emit('notification:count', {'unread_count': unread})
        
        return True
        
    except Exception as e:
        logger.error(f"WebSocket connection error: {str(e)}")
        return False


@socketio.on('disconnect')
def handle_disconnect():
    logger.debug("Client disconnected from WebSocket")


@socketio.on('notification:mark_read')
def handle_mark_notification_read(data):
    try:
        notification_id = data.get('notification_id')
        
        if not notification_id:
            emit('error', {'message': 'Notification ID is required'})
            return
        
        success = notification_interface.mark_read(str(notification_id))
        
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
    try:
        if not current_user.is_authenticated:
            emit('error', {'message': 'Unauthorized'})
            return

        user_id = current_user.id

        unread = notification_interface.get_unread_count(str(user_id))
        emit('notification:count', {'unread_count': unread})
        
    except Exception as e:
        logger.error(f"Error getting unread count: {str(e)}")
        emit('error', {'message': 'An error occurred'})
