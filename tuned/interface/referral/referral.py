import logging
from typing import Optional, Sequence, TYPE_CHECKING
from tuned.core.events import get_event_bus
from tuned.core.logging import get_logger
from tuned.dtos import ReferralResponseDTO, ReferralRedemptionResultDTO
from tuned.repository.protocols import(
    ReferralRepositoryProtocol, UserRepositoryProtocol,
    OrderRepositoryProtocol, ActivityLogRepositoryProtocol
)
from tuned.services.referral_service import ReferralService
from tuned.interface.protocols import ReferralInterfaceProtocol

if TYPE_CHECKING:
    from tuned.repository import Repository

logger: logging.Logger = get_logger(__name__)

class ReferralInterface(ReferralInterfaceProtocol):
    def __init__(
        self,
        repos: "Repository",
        service: Optional[ReferralService] = None,
    ) -> None:
        if service:
            self._service = service
        else:
            from tuned.interface.audit import AuditService
            self._audit = AuditService(repos=repos)
            self._service = ReferralService(
                user_repo=repos.user,
                referral_repo=repos.referral,
                order_repo=repos.order,
                audit_service=self._audit.activity_log
            )
        
        self._user_repo = repos.user
        self._referral_repo = repos.referral
    
    def get_by_id(self, id: str) -> Optional[ReferralResponseDTO]:
        return self._referral_repo.get_by_id(id)

    def get_by_referred_id(self, referred_id: str) -> Optional[ReferralResponseDTO]:
        return self._referral_repo.get_by_referred_id(referred_id)

    def get_by_code(self, code: str) -> Optional[ReferralResponseDTO]:
        return self._referral_repo.get_by_code(code)

    def get_active_by_referrer(self, referrer_id: str) -> Sequence[ReferralResponseDTO]:
        return self._referral_repo.get_active_by_referrer(referrer_id)
    
    def get_referral_growth(self, referrer_id: str) -> Sequence[tuple[str, float]]:
        return self._referral_repo.get_referral_growth(referrer_id)
    
    def count_monthly_completed_referrals(self, referrer_id: str, year: int, month: int) -> int:
        return self._referral_repo.count_monthly_completed_referrals(referrer_id, year, month)
            
    def process_signup(self, new_user_id: str, referral_code: str) -> None:
        self._service.process_signup_with_referral(new_user_id, referral_code)

    def reward_referrer(self, referred_id: str, order_value: float) -> None:
        reward_result = self._service.calculate_and_reward_commission(referred_id, order_value)
        if not reward_result:
            return

        referrer = self._user_repo.get_user_by_id(reward_result.referrer_id)
        
        payload = {
            "referrer_id": reward_result.referrer_id,
            "referred_id": reward_result.referred_id,
            "points_earned": reward_result.points_earned,
            "new_total": referrer.reward_points if referrer else reward_result.points_earned,
        }
        get_event_bus().emit("ReferralCommissionEarned", payload)
        logger.info(f"[ReferralInterface] Successfully rewarded {reward_result.points_earned} points to user {reward_result.referrer_id}")

    def redeem_points(
        self,
        user_id: str,
        order_id: str,
        points_to_redeem: int,
    ) -> ReferralRedemptionResultDTO:
        return self._service.redeem_points(user_id, order_id, points_to_redeem)
