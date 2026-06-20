from __future__ import annotations
from flask import current_app
from tuned.core.logging import get_logger
from tuned.models import User, Order, Payment
from tuned.dtos import InvoiceResponseDTO
from tuned.utils.auth import get_user_ip
from datetime import datetime
import logging
from typing import Any, Optional

logger: logging.Logger = get_logger(__name__)


def should_send_email(user_id: int, email_type: str = 'general') -> bool:    
    critical_emails = [
        'order_confirmation',
        'payment_receipt',
        'account_security',
        'password_reset',
        'email_verification'
    ]
    
    if email_type in critical_emails:
        logger.debug(f"Critical email type '{email_type}' - always sending")
        return True
    
    user = User.query.get(user_id)
    
    if not user or not user.email_preferences:
        logger.debug(f"No email preferences found for user {user_id}, defaulting to send")
        return True
    
    prefs = user.email_preferences
    
    if not user.notification_preferences or not user.notification_preferences.email_notifications:
        logger.debug(f"Email notifications globally disabled for user {user_id}")
        return False
    
    type_mapping = {
        'newsletter': prefs.newsletter,
        'promotional': prefs.promotional_emails,
        'product_updates': prefs.product_updates,
        'marketing': prefs.promotional_emails,
        'general': True
    }
    
    should_send = bool(type_mapping.get(email_type, True))
    
    if not should_send:
        logger.debug(f"Email type '{email_type}' disabled for user {user_id}")
    
    return should_send


def send_verification_email(user: User, raw_token: str) -> None:
    from tuned.tasks.email import send_transactional_email

    frontend_url = current_app.config.get('FRONTEND_URL', 'http://localhost:3000')
    verification_url = (
        f"{frontend_url}/auth/register/verify-email/confirm"
        f"?uid={user.id}&token={raw_token}"
    )
    expires_hours = current_app.config.get('EMAIL_VERIFICATION_TOKEN_EXPIRES_HOURS', 24)

    try:
        send_transactional_email.apply_async(
            kwargs={
                'to': user.email,
                'subject': 'Verify Your Email — TunedEssays',
                'template': 'verify_email',
                'context': {
                    'recipient_name': user.get_name(),
                    'verification_url': verification_url,
                    'support_email': current_app.config.get(
                        'MAIL_DEFAULT_SENDER', 'info@tunedessays.com'
                    ),
                    'current_year': datetime.now().year,
                    'expires_hours': expires_hours,
                },
                'sender': 'no-reply@tunedessays.com',
            },
            queue='email',
        )
        logger.info(f"[email_service] Verification email queued for user {user.id}")

    except Exception as exc:
        logger.error(
            f"[email_service] Failed to queue verification email for user {user.id}: {exc!r}"
        )


def send_welcome_email(user: User) -> None:
    from tuned.utils.email import send_async_email

    frontend_url = current_app.config.get('FRONTEND_URL', 'http://localhost:3000')
    dashboard_url = f"{frontend_url}/dashboard"
    support_url = f"{frontend_url}/support"
    
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

def send_invoice_email(user: User, invoice: Any) -> None:
    from tuned.utils.email import send_async_email

    frontend_url = current_app.config.get('FRONTEND_URL', 'http://localhost:3000')
    invoice_url = f"{frontend_url}/client/billing/invoices/{invoice.id}"
    
    send_async_email(
        to=user.email,
        subject=f'New Invoice Generated - {invoice.invoice_number}',
        template='client/invoice',
        recipient_name=user.get_name(),
        invoice_number=invoice.invoice_number,
        invoice_total=invoice.total,
        invoice_due_date=invoice.due_date.strftime('%Y-%m-%d'),
        invoice_url=invoice_url,
        support_email=current_app.config.get('MAIL_DEFAULT_SENDER'),
        current_year=datetime.now().year
    )
    
    logger.info(f"Invoice email sent to user {user.id} for invoice {invoice.invoice_number}")

def send_payment_client_marked_paid(client: User, order: Order, payment: Payment)-> None:
    from tuned.utils.email import send_async_email
    frontend_url = current_app.config.get('FRONTEND_URL', 'http://localhost:3000')
    order_url = f"{frontend_url}/client/orders/{order.id}"
    
    send_async_email(
        to=client.email,
        subject=f"Payment Proof Received - Order #{order.order_number}",
        template="client/payment_proof_submitted",
        client_name=client.get_name(),
        order_number=order.order_number,
        payment_method=payment.accepted_method.name if payment.accepted_method else "Manual Transfer",
        amount=payment.amount,
        proof_reference=payment.client_proof_reference,
        order_url=order_url,
        support_email=current_app.config.get('MAIL_DEFAULT_SENDER', 'support@tunedessays.com'),
        current_year=datetime.now().year
    )

    logger.info(f"Payment email sent to client {client.id} for payment {payment.id}")
            
def send_admin_payment_proof_submitted(admin: User, payment: Payment, client_name: str, order_number)-> None:
    from tuned.utils.email import send_async_email
    frontend_url = current_app.config.get('FRONTEND_URL', 'http://localhost:3000')    
    admin_verify_url = f"{frontend_url}/admin/orders/{order_number}"
    
    send_async_email(
        to=admin.email,
        subject=f"Action Required: Verify Payment for Order #{order_number}",
        template="admin/payment_proof_submitted",
        client_name=client_name,
        order_number=order_number,
        payment_method=payment.accepted_method.name if payment.accepted_method else "Manual Transfer",
        amount=payment.amount,
        proof_reference=payment.client_proof_reference,
        admin_verify_url=admin_verify_url,
        current_year=datetime.now().year
    )
    logger.info(f"Payment email sent to admin {admin.id} for payment {payment.id}")

def send_password_reset_email(user: User, reset_token: str) -> None:    
    from tuned.utils.email import send_async_email
    frontend_url = current_app.config.get('FRONTEND_URL', 'http://localhost:3000')
    reset_url = f"{frontend_url}/reset-password?token={reset_token}"
    
    request_ip = get_user_ip()
    request_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
    
    try:
        send_async_email(
            to=user.email,
            subject='Reset Your Password - Tuned Essays',
            template='client/password_reset',
            sender="no-reply@tunedessays.com",
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

def send_client_payment_verification_success_email(user: User, payment: Payment, order: Order) -> None:
    from tuned.utils.email import send_async_email
    frontend_url = current_app.config.get('FRONTEND_URL', 'http://localhost:3000')
    order_url = f"{frontend_url}/client/orders/{order.id}"
    invoice_url = f"{frontend_url}/client/billing/invoices/{order.invoice.id}" if getattr(order, 'invoice', None) else f"{frontend_url}/client/billing"
    
    send_async_email(
        to=user.email,
        subject=f"Payment Successful - Order #{order.order_number}",
        template="client/payment_confirmed",
        client_name=user.get_name(),
        order_number=order.order_number,
        payment_method=payment.accepted_method.name if payment.accepted_method else "Manual Transfer",
        amount_paid=payment.amount,
        transaction_id=payment.payment_id,
        payment_date=payment.admin_verified_at.strftime('%Y-%m-%d %H:%M:%S UTC') if payment.admin_verified_at else datetime.now().strftime('%Y-%m-%d'),
        due_date=order.due_date.strftime('%B %d, %Y') if order.due_date else "N/A",
        order_url=order_url,
        invoice_url=invoice_url,
        support_email=current_app.config.get('MAIL_DEFAULT_SENDER', 'support@tunedessays.com'),
        support_phone="+1 (800) 555-0199",
        company_name="Tuned Essays",
        current_year=datetime.now().year
    )

    logger.info(f"Payment verification success email sent to user {user.id}")
    
def send_client_payment_verification_failure_email(client: User, order_number: str, rejection_reason: str) -> None:
    from tuned.utils.email import send_async_email

    frontend_url = current_app.config.get('FRONTEND_URL', 'http://localhost:3000')
    order_url = f"{frontend_url}/client/orders/{order_number}"
    
    send_async_email(
        to=client.email,
        subject=f"Payment Verification Failed - Order #{order_number}",
        template="client/payment_rejected",
        client_name=client.get_name(),
        order_number=order_number,
        rejection_reason=rejection_reason,
        order_url=order_url,
        support_email=current_app.config.get('MAIL_DEFAULT_SENDER', 'support@tunedessays.com'),
        current_year=datetime.now().year
    )

    logger.info(f"Payment verification failure email sent to user {client.id}")

def send_invoice_created_email(client: User, invoice: InvoiceResponseDTO, order_number) -> None:
    from tuned.utils.email import send_async_email
    frontend_url = current_app.config.get('FRONTEND_URL', 'http://localhost:3000')
    invoice_url = f"{frontend_url}/client/billing/invoices/{invoice.id}"
    
    send_async_email(
        to=client.email,
        subject=f"New Invoice Generated - {invoice.invoice_number}",
        template="client/invoice_created",
        client_name=client.get_name(),
        order_number=order_number,
        invoice_number=invoice.invoice_number,
        subtotal=invoice.subtotal,
        discount=invoice.discount or 0.0,
        total=invoice.total,
        invoice_url=invoice_url,
        support_email=current_app.config.get('MAIL_DEFAULT_SENDER', 'support@tunedessays.com'),
        current_year=datetime.now().year
    )

    logger.info(f"Invoice created email sent to user {client.id} for invoice {invoice.id}")

def send_password_changed_email(user: User) -> None:
    from tuned.utils.email import send_async_email
    send_async_email(
        to=user.email,
        subject='Password Changed - Tuned Essays',
        template='client/verify_email',
        recipient_name=user.get_name(),
        verification_url='#',
        support_email=current_app.config.get('MAIL_DEFAULT_SENDER'),
        current_year=datetime.now().year
    )
    
    logger.info(f"Password changed email queued for user {user.id}")


def send_receipt_email(payment: Any, email_address: str) -> None:
    """Send payment receipt via email."""
    logger.info(f'Sending receipt email for payment {payment.id} to {email_address}')


def send_refund_request_email_admin(payment: Any, refund_amount: float, reason: str) -> None:
    """Send refund request notification to admin/finance team."""
    logger.info(f'Sending refund request email for payment {payment.id}: ${refund_amount:.2f}')


def send_email_change_confirmation(old_email: str, new_email: str, user_name: str) -> None:
    """Send email change confirmation to old email address."""
    logger.info(f'Sending email change confirmation: {old_email} -> {new_email}')


def send_newsletter_welcome_email(email: str, name: str) -> None:
    """Send newsletter welcome email."""
    logger.info(f'Sending newsletter welcome to {email}')


def send_newsletter_goodbye_email(email: str, name: str) -> None:
    """Send newsletter unsubscribe confirmation."""
    logger.info(f'Sending newsletter goodbye to {email}')


def send_payment_reminder_email(order: Any) -> None:
    """Send payment reminder for unpaid order."""
    logger.info(f'Sending payment reminder for order {order.id}')


def send_revision_request_email_admin(order: Any, revision_notes: str) -> None:
    from tuned.utils.email import send_async_email
    try:
        subject = f'Revision Request - {order.order_number}'
        html_body = f"""
        <h2>New Revision Request</h2>
        <p>Client: {order.client.get_name()} ({order.client.email})</p>
        <p>Order: {order.order_number} - {order.title}</p>
        <p>Revision Notes: {revision_notes}</p>
        <a href="{current_app.config.get('FRONTEND_URL', 'http://localhost:3000')}/admin/orders/{order.id}">View Order</a>
        """
        admins = User.query.filter_by(is_admin=True, is_active=True).all()
        for admin in admins:
            send_async_email(
                to=admin.email, 
                subject=subject, 
                template='generic_notification',
                body=html_body,
                current_year=datetime.now().year
            )
        logger.info(f'Revision request email sent for order {order.id}')
    except Exception as e:
        logger.error(f'Revision request email failed for order {order.id}: {str(e)}')
        raise


def send_deadline_extension_request_email_admin(order: Any, hours: int, reason: str) -> None:
    from tuned.utils.email import send_async_email
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
        admins = User.query.filter_by(is_admin=True, is_active=True).all()
        for admin in admins:
            send_async_email(
                to=admin.email, 
                subject=subject, 
                template='generic_notification',
                body=html_body,
                current_year=datetime.now().year
            )
        logger.info(f'Extension request email sent for order {order.id}')
    except Exception as e:
        logger.error(f'Extension request email failed for order {order.id}: {str(e)}')
        raise


def send_order_created_email_client(order: Any) -> None:
    from tuned.utils.email import send_async_email
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
        send_async_email(
            to=order.client.email, 
            subject=subject, 
            template='generic_notification',
            body=html_body,
            current_year=datetime.now().year
        )
        logger.info(f'Order created email sent to {order.client.email}')
    except Exception as e:
        logger.error(f'Order created email failed: {str(e)}')


def send_order_created_email_admin(order: Any) -> None:
    from tuned.utils.email import send_async_email
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
        admins = User.query.filter_by(is_admin=True, is_active=True).all()
        for admin in admins:
            send_async_email(
                to=admin.email, 
                subject=subject, 
                template='generic_notification',
                body=html_body,
                current_year=datetime.now().year
            )
        logger.info('New order email sent to admins')
    except Exception as e:
        logger.error(f'Order notification to admins failed: {str(e)}')


def send_refund_processed_email(client: User, order: Order, refund: Any) -> None:
    from tuned.utils.email import send_async_email
    try:
        subject = f"Refund Processed - Order #{order.order_number}"
        html_body = f"""
        <h2>Your refund has been processed</h2>
        <p>Dear {client.get_name()},</p>
        <p>A refund has been successfully processed for Order <strong>#{order.order_number}</strong>.</p>
        <p>Refund Amount: <strong>${refund.amount:.2f}</strong></p>
        <p>If you have any questions or require further assistance, please feel free to reach out to our support team.</p>
        <p>Best regards,</p>
        <p>Tuned Essays Team</p>
        """
        send_async_email(
            to=client.email,
            subject=subject,
            template="generic_notification",
            body=html_body,
            current_year=datetime.now().year
        )
        logger.info(f"Refund processed email sent to client {client.id} for refund {refund.id}")
    except Exception as e:
        logger.error(f"Failed to send refund processed email for user {client.id}: {str(e)}")
