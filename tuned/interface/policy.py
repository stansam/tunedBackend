from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
from tuned.core.logging import get_logger
from tuned.core.events import get_event_bus
from tuned.repository.exceptions import DatabaseError, NotFound
from tuned.dtos import ActivityLogCreateDTO
from tuned.utils.variables import Variables

if TYPE_CHECKING:
    from tuned.repository import Repository
    from tuned.interface import Services

logger = get_logger(__name__)

POLICY_VERSIONS = {
    "terms": "1.0.0",
    "privacy": "1.0.0",
    "refund": "1.0.0",
}

class LegalService:
    def __init__(self, repos: "Repository", interfaces: "Services") -> None:
        self._repo = repos.policy
        self._repos = repos
        self._interfaces = interfaces
        self._event_bus = get_event_bus()

    def get_policies(self) -> dict[str, str]:
        return {
            "termsVersion": POLICY_VERSIONS["terms"],
            "privacyVersion": POLICY_VERSIONS["privacy"],
            "refundVersion": POLICY_VERSIONS["refund"]
        }

    def check_status(self, user_id: str) -> bool:
        """
        Returns True if the user needs to accept policies (either no record exists
        or the recorded versions are outdated).
        """
        try:
            latest = self._repo.get_latest_for_user(user_id)
            if not latest:
                return True

            current_terms = POLICY_VERSIONS["terms"]
            current_privacy = POLICY_VERSIONS["privacy"]

            if latest.terms_version != current_terms or latest.privacy_version != current_privacy:
                return True

            return False
        except Exception as e:
            logger.error(f"Error checking policy status for user {user_id}: {str(e)}")
            raise DatabaseError(str(e))

    def accept_policies(
        self,
        user_id: str,
        terms_version: str,
        privacy_version: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> None:
        try:
            # Create DB acceptance log
            acceptance = self._repo.create(
                user_id=user_id,
                terms_version=terms_version,
                privacy_version=privacy_version,
                ip_address=ip_address,
                user_agent=user_agent
            )

            # Log audit activity
            self._interfaces.audit.activity_log.log(ActivityLogCreateDTO(
                user_id=user_id,
                action=Variables.POLICY_ACCEPTANCE_ACTION,
                entity_type=Variables.POLICY_ENTITY_TYPE,
                entity_id=str(acceptance.id),
                before=None,
                after={
                    "terms_version": terms_version,
                    "privacy_version": privacy_version,
                    "accepted_at": datetime.now(timezone.utc).isoformat(),
                    "ip_address": ip_address,
                },
                ip_address=ip_address,
                user_agent=user_agent,
                created_by=user_id,
            ))

            self._repo.save()

            # Emit event
            self._event_bus.emit("legal.policy_accepted", {
                "user_id": user_id,
                "terms_version": terms_version,
                "privacy_version": privacy_version,
                "ip_address": ip_address,
                "user_agent": user_agent
            })
        except Exception as e:
            logger.error(f"Error accepting policies for user {user_id}: {str(e)}")
            self._repo.rollback()
            raise DatabaseError(str(e))
