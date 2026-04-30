import logging
from typing import Optional, TYPE_CHECKING
from tuned.dtos.communication import NewsletterSubscribeDTO, NewsletterSubscriberResponseDTO
from tuned.repository.exceptions import DatabaseError, NotFound
from tuned.core.logging import get_logger

if TYPE_CHECKING:
    from tuned.repository import Repository
    from tuned.interface import Services

logger: logging.Logger = get_logger(__name__)

class NewsletterService:
    def __init__(self, repos: "Repository", services: "Services") -> None:
        self._repo = repos.newsletter
        self._services = services

    def subscribe(self, data: NewsletterSubscribeDTO, ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> NewsletterSubscriberResponseDTO:
        try:
            existing = self._repo.get_by_email(data.email)
            
            if existing:
                if existing.is_active:
                    return existing
                
                result = self._repo.update_status(existing.id, True, data.name)
                logger.info(f"Newsletter subscription reactivated for {data.email}")
                
                self._services.audit.log_activity(
                    action='newsletter_resubscribed',
                    entity_type='NewsletterSubscriber',
                    entity_id=result.id,
                    description=f'Newsletter subscription reactivated: {data.email}',
                    ip_address=ip_address,
                    user_agent=user_agent
                )
                
                self._send_confirmation(data.email, data.name or existing.name)
                return result

            result = self._repo.create(data)
            logger.info(f"New newsletter subscription for {data.email}")
            
            self._services.audit.log_activity(
                action='newsletter_subscribed',
                entity_type='NewsletterSubscriber',
                entity_id=result.id,
                description=f'New newsletter subscription: {data.email}',
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            self._send_confirmation(data.email, data.name or "")
            return result

        except DatabaseError as e:
            logger.error(f"Database error in newsletter subscription: {str(e)}")
            raise

    def _send_confirmation(self, email: str, name: str) -> None:
        try:
            from tuned.services.newsletter_service import send_newsletter_subscription_email
            send_newsletter_subscription_email(email, name)
        except Exception as e:
            logger.error(f"Failed to send newsletter confirmation email: {str(e)}")
