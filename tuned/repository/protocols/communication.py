from typing import Protocol, Optional, runtime_checkable, TYPE_CHECKING

if TYPE_CHECKING:
    from tuned.dtos.communication import NewsletterSubscribeDTO, NewsletterSubscriberResponseDTO

@runtime_checkable
class NewsletterRepositoryProtocol(Protocol):
    def get_by_email(self, email: str) -> Optional["NewsletterSubscriberResponseDTO"]: ...
    def create(self, data: "NewsletterSubscribeDTO") -> "NewsletterSubscriberResponseDTO": ...
    def update_status(self, subscriber_id: str, is_active: bool, name: Optional[str] = None) -> "NewsletterSubscriberResponseDTO": ...
