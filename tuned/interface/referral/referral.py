import logging
from tuned.services.referral_service import referral_service
from tuned.core.events import get_event_bus
from tuned.repository import repositories

logger = logging.getLogger(__name__)

class ReferralInterface:
    def __init__(self) -> None: 
        self._user_repo = repositories.user

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
