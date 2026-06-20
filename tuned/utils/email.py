from tuned.dtos.audit import EmailLogCreateDTO, EmailLogUpdateDTO
from flask import current_app, render_template
# from tuned.interface.audit import AuditService
from tuned.core.exceptions import DatabaseError
from tuned.utils.dependencies import get_services
from flask_mail import Mail, Message
from tuned.models.enums import EmailStatus
from tuned.extensions import db, mail
from typing import List, Optional, Dict, Any, cast
import logging
from datetime import datetime, timezone


logger = logging.getLogger(__name__)


def send_email(
    to: str | List[str],
    subject: str,
    template: str,
    sender: Optional[str] = None,
    **context: Any
) -> bool:
    recipients: List[str] = [to] if isinstance(to, str) else list(to)
    data = EmailLogCreateDTO(
        recipient=recipients[0] if recipients else '',
        subject=subject,
        template=template,
        user_id=None,
        order_id=None,
        created_by=None
    )
    try:
        email_log = get_services().audit.email_log.log(data)
        db.session.commit()
    except DatabaseError as e:
        db.session.rollback()
        logger.error(f"Failed to log email: {str(e)}")
        email_log = None
    
    try:
        html = render_template(f'emails/{template}.html', **context)
        
        msg = Message(
            subject=subject,
            recipients=cast(Any, recipients),
            html=html,
            sender=sender if sender else current_app.config['MAIL_DEFAULT_SENDER']
        )
        
        mail.send(msg)
        try:
            if email_log is not None:
                update_data = EmailLogUpdateDTO(
                    status=EmailStatus.SENT,
                    sent_at=datetime.now(timezone.utc)
                )
                _ =  get_services().audit.email_log.update_status(email_log.id, update_data)
                db.session.commit()
        except DatabaseError as e:
            db.session.rollback()
            logger.error(f"Failed to mark email as sent: {str(e)}")
        
        logger.info(f"Email sent successfully to {recipients[0]}: {subject}")
        return True
        
    except Exception as e:
        try:
            if email_log is not None:
                update_data = EmailLogUpdateDTO(
                    status=EmailStatus.FAILED,
                    error_message=str(e)
                )
                _ =  get_services().audit.email_log.update_status(email_log.id, update_data)
                db.session.commit()
        except DatabaseError as e:
            db.session.rollback()
            logger.error(f"Failed to mark email as failed: {str(e)}")
        
        logger.error(f"Failed to send email to {recipients[0]}: {str(e)}")
        return False


def send_async_email(to: str, subject: str, template: str, sender: Optional[str]=None, **context: Any) -> None:
    from tuned.tasks.email import send_transactional_email
    send_transactional_email.delay(to, subject, template, context, sender)


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
