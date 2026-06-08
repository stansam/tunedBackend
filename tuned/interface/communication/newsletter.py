import logging
from typing import Optional, TYPE_CHECKING
from tuned.dtos import NewsletterSubscribeDTO, NewsletterSubscriberResponseDTO, ActivityLogCreateDTO
from tuned.repository.exceptions import DatabaseError, NotFound
from tuned.core.logging import get_logger
from tuned.utils.variables import Variables
if TYPE_CHECKING:
    from tuned.repository import Repository
    from tuned.interface import Services

logger: logging.Logger = get_logger(__name__)

class NewsletterService:
    def __init__(self, repos: "Repository", services: "Services") -> None:
        self._repo = repos.newsletter
        self._services = services

    def subscribe(self, data: NewsletterSubscribeDTO, ip_address: Optional[str] = "system", user_agent: Optional[str] = "system") -> NewsletterSubscriberResponseDTO:
        try:
            existing = self._repo.get_by_email(data.email)
            
            if existing:
                if existing.is_active:
                    return NewsletterSubscriberResponseDTO.from_model(existing)
                
                result = self._repo.update_status(str(existing.id), True, data.name)
                logger.info(f"Newsletter subscription reactivated for {data.email}")
                
                self._services.audit.activity_log.log(
                    ActivityLogCreateDTO(
                        action=Variables.NEWSLETTER_SUBSCRIBER_RESUBSCRIBED,
                        entity_type=Variables.NEWSLETTER_SUBSCRIBER_ENTITY_TYPE,
                        entity_id=str(result.id),
                        before=existing,
                        after=result,
                        ip_address=ip_address,
                        user_agent=user_agent
                    )
                )

                self._repo.save()
                
                self._send_confirmation(data.email, data.name if data.name else existing.name if existing.name else "")
                return NewsletterSubscriberResponseDTO.from_model(result)

            result = self._repo.create(data)
            logger.info(f"New newsletter subscription for {data.email}")
            
            self._services.audit.activity_log.log(
                ActivityLogCreateDTO(
                    action=Variables.NEWSLETTER_SUBSCRIBER_SUBSCRIBED,
                    entity_type=Variables.NEWSLETTER_SUBSCRIBER_ENTITY_TYPE,
                    entity_id=str(result.id),
                    before=None,
                    after=result,
                    ip_address=ip_address,
                    user_agent=user_agent
                )
            )

            self._repo.save()

            self._send_confirmation(data.email, data.name or "")
            return NewsletterSubscriberResponseDTO.from_model(result)

        except DatabaseError as e:
            logger.error(f"Database error in newsletter subscription: {str(e)}")
            raise

    def _send_confirmation(self, email: str, name: str) -> None:
        try:
            from tuned.services.newsletter_service import send_newsletter_subscription_email
            send_newsletter_subscription_email(email, name)
        except Exception as e:
            logger.error(f"Failed to send newsletter confirmation email: {str(e)}")
