"""
Newsletter service module.

Handles newsletter subscription email operations.
"""
from flask import current_app
from tuned.utils.email import send_async_email
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def send_newsletter_subscription_email(email: str, name: str = None) -> None:
    """
    Send newsletter subscription confirmation email.
    
    Args:
        email: Subscriber email address
        name: Subscriber name (optional, defaults to "Subscriber")
    """
    # Build URLs
    frontend_url = current_app.config.get('FRONTEND_URL', 'http://localhost:3000')
    blog_url = f"{frontend_url}/blog"
    services_url = f"{frontend_url}/services"
    unsubscribe_url = f"{frontend_url}/newsletter/unsubscribe?email={email}"
    
    # Send email asynchronously
    send_async_email(
        to=email,
        subject='Welcome to Tuned Essays Newsletter!',
        template='client/newsletter_subscription',
        recipient_name=name or 'Subscriber',
        blog_url=blog_url,
        services_url=services_url,
        unsubscribe_url=unsubscribe_url,
        support_email=current_app.config.get('MAIL_DEFAULT_SENDER'),
        company_name='Tuned Essays',
        current_year=datetime.now().year
    )
    
    logger.info(f"Newsletter subscription email queued for {email}")
