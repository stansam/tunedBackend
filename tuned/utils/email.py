from flask import current_app, render_template
from flask_mail import Mail, Message
from tuned.models.audit import EmailLog
from tuned.extensions import db, mail
from typing import List, Optional, Dict, Any
import logging


logger = logging.getLogger(__name__)


def send_email(
    to: str | List[str],
    subject: str,
    template: str,
    sender: Optional[str] = None,
    **context: Any
) -> bool:
    recipients = [to] if isinstance(to, str) else to
    
    email_log = EmailLog.log_email(
        recipient=recipients[0] if recipients else '',
        subject=subject,
        template=template
    )
    
    try:
        html = render_template(f'emails/{template}.html', **context)
        
        msg = Message(
            subject=subject,
            recipients=recipients,
            html=html,
            sender=sender if sender else current_app.config['MAIL_DEFAULT_SENDER']
        )
        
        mail.send(msg)
        
        email_log.mark_sent()
        
        logger.info(f"Email sent successfully to {recipients[0]}: {subject}")
        return True
        
    except Exception as e:
        email_log.mark_failed(str(e))
        
        logger.error(f"Failed to send email to {recipients[0]}: {str(e)}")
        return False


def send_async_email(to: str | List[str], subject: str, template: str, sender: Optional[str]=None, **context: Any) -> None:
    from tuned.tasks.email import send_transactional_email
    if sender is None:
        send_transactional_email.delay(to, subject, template, context)
    else:
        send_transactional_email.delay(to, subject, template, sender, context)


def send_bulk_emails(
    recipients: List[str],
    subject: str,
    template: str,
    **context: Any
) -> Dict[str, int]:
    results = {'sent': 0, 'failed': 0}
    
    for recipient in recipients:
        success = send_email(recipient, subject, template, **context)
        if success:
            results['sent'] += 1
        else:
            results['failed'] += 1
    
    return results


def send_test_email(to: str) -> bool:
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
