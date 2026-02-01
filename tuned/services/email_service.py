"""
Email service module.

High-level email operations for authentication workflows.
Integrates with email utility functions and Celery for async sending.
"""
from flask import current_app
from tuned.utils.email import send_async_email
from tuned.models.user import User
from datetime import datetime
import logging


logger = logging.getLogger(__name__)


def send_verification_email(user: User, verification_token: str) -> None:
    """
    Send email verification link to user.
    
    Args:
        user: User model instance
        verification_token: Verification token from tokens utility
    """
    # Build verification URL
    frontend_url = current_app.config.get('FRONTEND_URL', 'http://localhost:3000')
    verification_url = f"{frontend_url}/verify-email?token={verification_token}"
    
    # Send email asynchronously
    send_async_email(
        to=user.email,
        subject='Verify Your Email - Tuned Essays',
        template='client/verify_email',
        recipient_name=user.get_name(),
        verification_url=verification_url,
        support_email=current_app.config.get('MAIL_DEFAULT_SENDER'),
        company_name='Tuned Essays',
        current_year=datetime.now().year
    )
    
    logger.info(f"Verification email queued for user {user.id}")


def send_welcome_email_delayed(user: User) -> None:
    """
    Send welcome email with delay (15-30 minutes after email verification).
    
    Uses Celery countdown to delay execution.
    
    Args:
        user: User model instance
    """
    from tuned.celery_app import celery_app
    import random
    
    # Random delay between 15-30 minutes (900-1800 seconds)
    delay_seconds = random.randint(900, 1800)
    
    @celery_app.task
    def _send_welcome_task(user_id):
        """Celery task for sending welcome email."""
        from tuned import create_app
        from tuned.models.user import User
        
        app = create_app()
        with app.app_context():
            user = User.query.get(user_id)
            if user:
                send_welcome_email(user)
    
    # Queue the task with delay
    _send_welcome_task.apply_async(args=[user.id], countdown=delay_seconds)
    
    logger.info(f"Welcome email scheduled for user {user.id} with {delay_seconds}s delay")


def send_welcome_email(user: User) -> None:
    """
    Send welcome email to user (called by delayed task).
    
    Args:
        user: User model instance
    """
    # Build dashboard URL
    frontend_url = current_app.config.get('FRONTEND_URL', 'http://localhost:3000')
    dashboard_url = f"{frontend_url}/dashboard"
    support_url = f"{frontend_url}/support"
    
    # Send email asynchronously
    send_async_email(
        to=user.email,
        subject='Welcome to Tuned Essays!',
        template='client/welcome',
        recipient_name=user.get_name(),
        dashboard_url=dashboard_url,
        support_url=support_url,
        support_email=current_app.config.get('MAIL_DEFAULT_SENDER'),
        current_year=datetime.now().year
    )
    
    logger.info(f"Welcome email sent to user {user.id}")


def send_password_reset_email(user: User, reset_token: str) -> None:
    """
    Send password reset link to user.
    
    Args:
        user: User model instance
        reset_token: Password reset token from tokens utility
    """
    from flask import request
    from tuned.utils.auth import get_user_ip
    
    # Build reset URL
    frontend_url = current_app.config.get('FRONTEND_URL', 'http://localhost:3000')
    reset_url = f"{frontend_url}/reset-password?token={reset_token}"
    
    # Get request info for security display
    request_ip = get_user_ip()
    request_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
    
    # Send email asynchronously
    try:
        send_async_email(
            to=user.email,
            subject='Reset Your Password - Tuned Essays',
            template='client/password_reset',
            recipient_name=user.get_name(),
            reset_url=reset_url,
            request_ip=request_ip,
            request_time=request_time,
            support_email=current_app.config.get('MAIL_DEFAULT_SENDER'),
            current_year=datetime.now().year
        )
        logger.info(f"Password reset email queued for user {user.id}")
    except Exception as e:
        logger.error(f'Password reset email failed for user {user.id}: {str(e)}')
        raise


def send_password_changed_email(user: User) -> None:
    """
    Send confirmation email after password change.
    
    Args:
        user: User model instance
    """
    # For now, we can reuse a simple email or create a dedicated template
    # This is a simple confirmation, no action needed
    from tuned.utils.email import send_async_email
    
    send_async_email(
        to=user.email,
        subject='Password Changed - Tuned Essays',
        template='client/verify_email',  # Reuse template structure
        recipient_name=user.get_name(),
        verification_url='#',  # No action needed
        support_email=current_app.config.get('MAIL_DEFAULT_SENDER'),
        current_year=datetime.now().year
    )
    
    logger.info(f"Password changed email queued for user {user.id}")


def send_receipt_email(payment, email_address):
    """Send payment receipt via email."""
    logger.info(f'Sending receipt email for payment {payment.id} to {email_address}')
    # Stubimplementation - in production, send actual email
    pass


def send_refund_request_email_admin(payment, refund_amount, reason):
    """Send refund request notification to admin/finance team."""
    logger.info(f'Sending refund request email for payment {payment.id}: ${refund_amount:.2f}')
    # Stub implementation
    pass


def send_password_changed_email(user):
    """Send password change confirmation email."""
    logger.info(f'Sending password changed email to user {user.id}')
    # Stub implementation
    pass


def send_email_change_confirmation(old_email, new_email, user_name):
    """Send email change confirmation to old email address."""
    logger.info(f'Sending email change confirmation: {old_email} -> {new_email}')
    # Stub implementation
    pass


def send_newsletter_welcome_email(email, name):
    """Send newsletter welcome email."""
    logger.info(f'Sending newsletter welcome to {email}')
    # Stub implementation
    pass


def send_newsletter_goodbye_email(email, name):
    """Send newsletter unsubscribe confirmation."""
    logger.info(f'Sending newsletter goodbye to {email}')
    # Stub implementation
    pass


def send_payment_reminder_email(order):
    """Send payment reminder for unpaid order."""
    logger.info(f'Sending payment reminder for order {order.id}')
    # Stub implementation
    pass


def send_revision_request_email_admin(order, revision_notes: str) -> None:
    """Send email to admins when client requests a revision."""
    try:
        subject = f'Revision Request - {order.order_number}'
        html_body = f"""
        <h2>New Revision Request</h2>
        <p>Client: {order.client.get_name()} ({order.client.email})</p>
        <p>Order: {order.order_number} - {order.title}</p>
        <p>Revision Notes: {revision_notes}</p>
        <a href="{current_app.config.get('FRONTEND_URL', 'http://localhost:3000')}/admin/orders/{order.id}">View Order</a>
        """
        from tuned.models.user import User
        admins = User.query.filter_by(is_admin=True, is_active=True).all()
        for admin in admins:
            send_async_email(to=admin.email, subject=subject, html_body=html_body)
        logger.info(f'Revision request email sent for order {order.id}')
    except Exception as e:
        logger.error(f'Revision request email failed for order {order.id}: {str(e)}')
        raise


def send_deadline_extension_request_email_admin(order, hours: int, reason: str) -> None:
    """Send email to admins when client requests deadline extension."""
    try:
        subject = f'Deadline Extension Request - {order.order_number}'
        html_body = f"""
        <h2>Deadline Extension Request</h2>
        <p>Client: {order.client.get_name()} ({order.client.email})</p>
        <p>Order: {order.order_number} - {order.title}</p>
        <p>Current Due Date: {order.due_date.strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
        <p>Requested Extension: {hours} hours</p>
        <p>Reason: {reason}</p>
        <a href="{current_app.config.get('FRONTEND_URL', 'http://localhost:3000')}/admin/orders/{order.id}">View Order</a>
        """
        from tuned.models.user import User
        admins = User.query.filter_by(is_admin=True, is_active=True).all()
        for admin in admins:
            send_async_email(to=admin.email, subject=subject, html_body=html_body)
        logger.info(f'Extension request email sent for order {order.id}')
    except Exception as e:
        logger.error(f'Extension request email failed for order {order.id}: {str(e)}')
        raise


def send_order_created_email_client(order) -> None:
    """Send order confirmation email to client."""
    try:
        subject = f'Order Confirmation - {order.order_number}'
        html_body = f"""
        <h2>Thank you for your order!</h2>
        <p>Order Number: {order.order_number}</p>
        <p>Title: {order.title}</p>
        <p>Total: ${order.total_price:.2f}</p>
        <p>Due Date: {order.due_date.strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
        <a href="{current_app.config.get('FRONTEND_URL', 'http://localhost:3000')}/orders/{order.id}">View Order</a>
        """
        send_async_email(to=order.client.email, subject=subject, html_body=html_body)
        logger.info(f'Order created email sent to {order.client.email}')
    except Exception as e:
        logger.error(f'Order created email failed: {str(e)}')


def send_order_created_email_admin(order) -> None:
    """Send new order notification to admins."""
    try:
        subject = f'New Order - {order.order_number}'
        html_body = f"""
        <h2>New Order Received</h2>
        <p>Client: {order.client.get_name()} ({order.client.email})</p>
        <p>Order: {order.order_number} - {order.title}</p>
        <p>Total: ${order.total_price:.2f}</p>
        <p>Due Date: {order.due_date.strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
        <a href="{current_app.config.get('FRONTEND_URL', 'http://localhost:3000')}/admin/orders/{order.id}">View Order</a>
        """
        from tuned.models.user import User
        admins = User.query.filter_by(is_admin=True, is_active=True).all()
        for admin in admins:
            send_async_email(to=admin.email, subject=subject, html_body=html_body)
        logger.info('New order email sent to admins')
    except Exception as e:
        logger.error(f'Order notification to admins failed: {str(e)}')
