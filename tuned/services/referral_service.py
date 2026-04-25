import logging
from typing import Optional, Dict, Any
from tuned.models.enums import ReferralStatus
from tuned.models.referral import Referral
from tuned.repository import repositories

logger = logging.getLogger(__name__)

class ReferralService:
    def __init__(self):
        self.COMMISSION_PERCENTAGE = 0.10 # TODO: Implement dynamic commission percentage(default for now).
        self._user_repo = repositories.user
        self._referral_repo = repositories.referral


    def process_signup_with_referral(self, new_user_id: str, referral_code: str) -> Optional[Referral]:
        referrer = self._user_repo.get_by_referral_code(referral_code)
        if not referrer:
            logger.warning(f"[ReferralService] Invalid referral code '{referral_code}' used by user {new_user_id}")
            return None
            
        referrer_id = str(referrer.id)
        if referrer_id == new_user_id:
            logger.warning(f"[ReferralService] Self-referral attempt by user {new_user_id}")
            return None
            
        existing = self._referral_repo.get_by_referred_id(new_user_id)
        if existing:
            logger.warning(f"[ReferralService] User {new_user_id} is already referred by {existing.referrer_id}")
            return existing
            
        referral = self._referral_repo.create(
            referrer_id=referrer_id,
            referred_id=new_user_id,
            code=referral_code
        )
        logger.info(f"[ReferralService] Created PENDING referral {referral.id} for referrer {referrer_id}")
        return referral

    def calculate_and_reward_commission(self, referred_id: str, order_value: float) -> Optional[Dict[str, Any]]:
        referral = self._referral_repo.get_by_referred_id(referred_id)
        if not referral:
            return None
            
        if referral.status not in [ReferralStatus.PENDING, ReferralStatus.ACTIVE]:
            logger.debug(f"[ReferralService] Referral {referral.id} is already {referral.status.value}, skipping reward.")
            return None
            
        commission_earned = round(order_value * self.COMMISSION_PERCENTAGE, 2)
        if commission_earned <= 0:
            return None

        return {
            "referral_id": str(referral.id),
            "referrer_id": referral.referrer_id,
            "referred_id": referred_id,
            "commission_earned": commission_earned,
            "new_status": ReferralStatus.COMPLETED
        }

referral_service = ReferralService()
