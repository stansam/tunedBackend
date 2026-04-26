import logging
from typing import Optional
from tuned.services.referral_service import referral_service
from tuned.core.events import get_event_bus
from tuned.repository import repositories
from tuned.core.logging import get_logger
from tuned.dtos import ReferralResponseDTO

logger: logging.Logger = get_logger(__name__)

class ReferralInterface:
    def __init__(self) -> None: 
        self._user_repo = repositories.user
        self._referral_repo = repositories.referral
    
    def get_by_id(self, id: str) -> Optional[ReferralResponseDTO]:
        try:
            referral = self._referral_repo.get_by_id(id)
            # if not referral:
            #     return None
            return referral
        except Exception as e:
            logger.error(f"[ReferralInterface] Error in get_by_id: {e}")
    def get_by_referred_id(self, referred_id: str) -> Optional[ReferralResponseDTO]:
        try:
            return self._referral_repo.get_by_referred_id(referred_id)
        except Exception as e:
            logger.error(f"[ReferralInterface] Error in get_by_referred_id: {e}")

    def get_by_code(self, code: str) -> Optional[ReferralResponseDTO]:
        try:
            return self._referral_repo.get_by_code(code)
        except Exception as e:
            logger.error(f"[ReferralInterface] Error in get_by_code: {e}")

    def get_active_by_referrer(self, referrer_id: str) -> Optional[ReferralResponseDTO]:
        try:
            return self._referral_repo.get_active_by_referrer(referrer_id)
        except Exception as e:
            logger.error(f"[ReferralInterface] Error in get_active_by_referrer: {e}")
    
    def get_referral_growth(self, referrer_id: str) -> list[tuple[str, float]]:
        try:
            return self._referral_repo.get_referral_growth(referrer_id)
        except Exception as e:
            logger.error(f"[ReferralInterface] Error in get_referral_growth: {e}")
    
    def count_monthly_completed_referrals(self, referrer_id: str, year: int, month: int) -> Optional[int]:
        try:
            return self._referral_repo.count_monthly_completed_referrals(referrer_id, year, month)
        except Exception as e:
            logger.error(f"[ReferralInterface] Error in count_monthly_completed_referrals: {e}")
            
    def process_signup(self, new_user_id: str, referral_code: str) -> None:
        try:
            referral_service.process_signup_with_referral(new_user_id, referral_code)
        except Exception as e:
            logger.error(f"[ReferralInterface] Error in process_signup: {e}")

    def reward_referrer(self, referred_id: str, order_value: float) -> None:
        try:
            reward_result = referral_service.calculate_and_reward_commission(referred_id, order_value)
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

        except Exception as e:
            logger.error(f"[ReferralInterface] Failed to reward referrer: {e}")
            raise

    def redeem_points(self, user_id: str, order_id: str, points_to_redeem: int) -> dict:
        try:
            return referral_service.redeem_points(user_id, order_id, points_to_redeem)
        except Exception as e:
            logger.error(f"[ReferralInterface] Failed to redeem points: {e}")
            raise
