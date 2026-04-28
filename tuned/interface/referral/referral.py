import logging
from typing import Optional, Sequence
from tuned.services.referral_service import referral_service
from tuned.core.events import get_event_bus
from tuned.repository import repositories
from tuned.core.logging import get_logger
from tuned.dtos import ReferralResponseDTO, ReferralRedemptionResultDTO
from tuned.repository.protocols import ReferralRepositoryProtocol, UserRepositoryProtocol
from tuned.services.referral_service import ReferralService

logger: logging.Logger = get_logger(__name__)

from tuned.interface.protocols import ReferralInterfaceProtocol

class ReferralInterface(ReferralInterfaceProtocol):
    def __init__(
        self,
        service: Optional[ReferralService] = None,
        user_repo: Optional[UserRepositoryProtocol] = None,
        referral_repo: Optional[ReferralRepositoryProtocol] = None,
    ) -> None:
        self._service = service or referral_service
        self._user_repo = user_repo or repositories.user
        self._referral_repo = referral_repo or repositories.referral
    
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
    
    def count_monthly_completed_referrals(self, referrer_id: str, year: int, month: int) -> Optional[int]:
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
