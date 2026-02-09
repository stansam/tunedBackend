"""
Email sending utilities with Flask-Mail integration.

Provides production-ready email sending with:
- Template rendering
- Async sending via Celery
- Error handling and retry logic
- Email logging to database
"""
from flask import current_app, render_template
from flask_mail import Mail, Message
from tuned.models.audit import EmailLog
from tuned.extensions import db, mail
from tuned.tasks.email import send_email_task
from typing import List, Optional, Dict, Any
import logging


logger = logging.getLogger(__name__)


def send_email(
    to: str | List[str],
    subject: str,
    template: str,
    **context: Any
) -> bool:
    """
    Send an email synchronously.
    
    Args:
        to: Recipient email address(es)
        subject: Email subject
        template: Template name (without .html extension) from templates/emails/
        **context: Template context variables
        
    Returns:
        bool: True if sent successfully, False otherwise
        
    Example:
        send_email(
            to='user@example.com',
            subject='Welcome!',
            template='client/welcome',
            recipient_name='John Doe',
            dashboard_url='https://example.com/dashboard'
        )
    """
    # Ensure recipient is a list
    recipients = [to] if isinstance(to, str) else to
    
    # Create email log entry
    email_log = EmailLog.log_email(
        recipient=recipients[0] if recipients else '',
        subject=subject,
        template=template
    )
    
    try:
        # Render HTML template
        html = render_template(f'emails/{template}.html', **context)
        
        # Create message
        msg = Message(
            subject=subject,
            recipients=recipients,
            html=html,
            sender=current_app.config['MAIL_DEFAULT_SENDER']
        )
        
        # Send email
        mail.send(msg)
        
        # Mark as sent
        email_log.mark_sent()
        
        logger.info(f"Email sent successfully to {recipients[0]}: {subject}")
        return True
        
    except Exception as e:
        # Mark as failed
        email_log.mark_failed(str(e))
        
        logger.error(f"Failed to send email to {recipients[0]}: {str(e)}")
        return False


def send_async_email(to: str | List[str], subject: str, template: str, **context: Any) -> None:
    """
    Send an email asynchronously using Celery.
    
    Args:
        to: Recipient email address(es)
        subject: Email subject
        template: Template name
        **context: Template context variables
        
    Example:
        send_async_email(
            to='user@example.com',
            subject='Account Verified',
            template='client/email_verified',
            recipient_name='John'
        )
    """
    
    # Queue the task
    send_email_task.delay(to, subject, template, context)


def send_bulk_emails(
    recipients: List[str],
    subject: str,
    template: str,
    **context: Any
) -> Dict[str, int]:
    """
    Send the same email to multiple recipients.
    
    Args:
        recipients: List of recipient email addresses
        subject: Email subject
        template: Template name
        **context: Template context variables
        
    Returns:
        dict: {'sent': count, 'failed': count}
        
    Example:
        results = send_bulk_emails(
            recipients=['user1@example.com', 'user2@example.com'],
            subject='Newsletter',
            template='admin/newsletter',
            content='...'
        )
    """
    results = {'sent': 0, 'failed': 0}
    
    for recipient in recipients:
        success = send_email(recipient, subject, template, **context)
        if success:
            results['sent'] += 1
        else:
            results['failed'] += 1
    
    return results


def send_test_email(to: str) -> bool:
    """
    Send a test email to verify email configuration.
    
    Args:
        to: Test recipient email
        
    Returns:
        bool: True if sent successfully
        
    Example:
        success = send_test_email('admin@example.com')
    """
    try:
        msg = Message(
            subject='Test Email - Tuned Essays',
            recipients=[to],
            body='This is a test email to verify email configuration is working correctly.',
            sender=current_app.config['MAIL_DEFAULT_SENDER']
        )
        
        mail.send(msg)
        logger.info(f"Test email sent successfully to {to}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send test email: {str(e)}")
        return False
