"""
Notification service module.

Handles creation and delivery of in-app notifications.
Integrates with SocketIO for real-time updates.
"""
from tuned.models.communication import Notification
from tuned.models.enums import NotificationType
from tuned.models.user import User
from tuned.extensions import db
from typing import Optional
import logging


logger = logging.getLogger(__name__)


def should_send_notification(user_id: int, notification_category: str = 'general') -> bool:
    """
    Check if a notification should be sent based on user preferences.
    
    Respects user notification preferences while defaulting to True
    if preferences don't exist (backward compatible).
    
    Args:
        user_id: User ID to check preferences for
        notification_category: Category of notification (order_updates, payment_notifications, etc.)
        
    Returns:
        bool: True if notification should be sent, False otherwise
    """
    from tuned.models.user import User
    
    user = User.query.get(user_id)
    
    # Default to True if user not found or preferences don't exist (backward compatible)
    if not user or not user.notification_preferences:
        logger.debug(f"No preferences found for user {user_id}, defaulting to send notification")
        return True
    
    prefs = user.notification_preferences
    
    # Map category to preference field
    category_mapping = {
        'order_updates': prefs.order_updates,
        'payment': prefs.payment_notifications,
        'delivery': prefs.delivery_notifications,
        'revision': prefs.revision_updates,
        'extension': prefs.extension_updates,
        'comment': prefs.comment_notifications,
        'support': prefs.support_ticket_updates,
        'marketing': prefs.marketing_emails,
        'general': True  # General notifications always sent
    }
    
    # Check if push notifications are enabled globally
    if not prefs.push_notifications:
        logger.debug(f"Push notifications disabled for user {user_id}")
        return False
    
    # Check category-specific preference
    should_send = category_mapping.get(notification_category, True)
    
    if not should_send:
        logger.debug(f"Notification category '{notification_category}' disabled for user {user_id}")
    
    return should_send



def create_notification(
    user_id: int,
    title: str,
    message: str,
    type: NotificationType = NotificationType.INFO,
    link: Optional[str] = None,
    category: str = 'general'
) -> Optional[Notification]:
    """
    Create a new notification for a user.
    
    Checks user preferences before creating notification.
    
    Args:
        user_id: User ID to notify
        title: Notification title
        message: Notification message
        type: Notification type (info, success, warning, error)
        link: Optional link URL
        category: Notification category for preference checking
        
    Returns:
        Notification: Created notification instance, or None if user has disabled this category
    """
    # Check preferences before creating notification
    if not should_send_notification(user_id, category):
        logger.info(f"Skipping notification for user {user_id} (category: {category} disabled)")
        return None
    
    notification = Notification(
        user_id=user_id,
        title=title,
        message=message,
        type=type,
        link=link,
        is_read=False
    )
    
    db.session.add(notification)
    db.session.commit()
    
    logger.info(f"Notification created for user {user_id}: {title}")
    
    # Emit via SocketIO
    try:
        emit_notification_via_socket(user_id, notification)
    except Exception as e:
        logger.error(f"Failed to emit notification via socket: {str(e)}")
    
    return notification


def create_welcome_notification(user: User) -> Notification:
    """
    Create welcome notification after user registration.
    
    Args:
        user: User model instance
        
    Returns:
        Notification: Created notification
    """
    return create_notification(
        user_id=user.id,
        title='Welcome to Tuned Essays!',
        message='Thank you for joining us. Please verify your email to get started.',
        type=NotificationType.INFO,
        link='/profile'
    )


def create_email_verified_notification(user: User) -> Notification:
    """
    Create notification after email verification.
    
    Args:
        user: User model instance
        
    Returns:
        Notification: Created notification
    """
    return create_notification(
        user_id=user.id,
        title='Email Verified!',
        message='Your email has been successfully verified. You can now access all features.',
        type=NotificationType.SUCCESS,
        link='/dashboard'
    )


def create_password_changed_notification(user: User) -> Notification:
    """
    Create notification after password change.
    
    Args:
        user: User model instance
        
    Returns:
        Notification: Created notification
    """
    return create_notification(
        user_id=user.id,
        title='Password Changed',
        message='Your password has been successfully updated. If this wasn\'t you, please contact support immediately.',
        type=NotificationType.WARNING,
        link='/profile/security'
    )


def emit_notification_via_socket(user_id: int, notification: Notification) -> None:
    """
    Emit notification to user via SocketIO.
    
    Args:
        user_id: User ID to emit to
        notification: Notification instance
    """
    from tuned.extensions import socketio
    
    # Emit to user's room
    socketio.emit(
        'notification:new',
        notification.to_dict(),
        room=f'user_{user_id}'
    )
    
    logger.debug(f"Notification emitted via SocketIO to user {user_id}")


def mark_notification_as_read(notification_id: int) -> bool:
    """
    Mark a notification as read.
    
    Args:
        notification_id: Notification ID
        
    Returns:
        bool: True if successful, False otherwise
    """
    notification = Notification.query.get(notification_id)
    
    if not notification:
        return False
    
    notification.is_read = True
    db.session.commit()
    
    logger.debug(f"Notification {notification_id} marked as read")
    return True


def mark_all_as_read(user_id: int) -> int:
    """
    Mark all notifications as read for a user.
    
    Args:
        user_id: User ID
        
    Returns:
        int: Number of notifications marked as read
    """
    count = Notification.query.filter_by(
        user_id=user_id,
        is_read=False
    ).update({'is_read': True})
    
    db.session.commit()
    
    logger.info(f"Marked {count} notifications as read for user {user_id}")
    return count


def get_unread_count(user_id: int) -> int:
    """
    Get count of unread notifications for a user.
    
    Args:
        user_id: User ID
        
    Returns:
        int: Count of unread notifications
    """
    return Notification.query.filter_by(
        user_id=user_id,
        is_read=False
    ).count()
