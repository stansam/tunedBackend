import logging
from typing import Optional
from tuned.models.enums import ReferralStatus
from tuned.dtos import ReferralResponseDTO, RewardCalculationResultDTO, ActivityLogCreateDTO, UpdateUserDTO
from tuned.utils.variables import Variables
from tuned.repository import repositories
from tuned.interface.audit import audit_service
from tuned.core.logging import get_logger

logger: logging.Logger = get_logger(__name__)

class ReferralService:
    def __init__(self):
        self.COMMISSION_PERCENTAGE = 0.10 # 10% of order value
        self.POINT_USD_VALUE = 0.4 # 1 point = $0.4
        self._user_repo = repositories.user
        self._referral_repo = repositories.referral
        self._log = audit_service.activity_log

    def process_signup_with_referral(self, new_user_id: str, referral_code: str) -> Optional[ReferralResponseDTO]:
        try:
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
            log_dto = ActivityLogCreateDTO(
                action=Variables.REFERRAL_SIGNUP_ACTION,
                user_id=new_user_id,
                entity_type=Variables.ENTITY_TYPE_REFERRAL,
                entity_id=referral.id,
                after=referral,
                ip_address="system",
                user_agent="system"
            )
            self._log.log(log_dto)
            logger.info(f"[ReferralService] Created PENDING referral {referral.id} for referrer {referrer_id}")
            return referral
        except Exception as e:
            logger.error(f"[ReferralService] process_signup_with_referral failed: {e}")
            raise

    def calculate_and_reward_commission(self, referred_id: str, order_value: float) -> Optional[RewardCalculationResultDTO]:
        try:
            referral = self._referral_repo.get_by_referred_id(referred_id)
            if not referral:
                return None
                
            if referral.status not in [ReferralStatus.PENDING, ReferralStatus.ACTIVE]:
                logger.debug(f"[ReferralService] Referral {referral.id} is already {referral.status}, skipping reward.")
                return None
                
            commission_usd = order_value * self.COMMISSION_PERCENTAGE
            points_earned = int(commission_usd / self.POINT_USD_VALUE)
            
            if points_earned <= 0:
                return None
            
            new_status = ReferralStatus.COMPLETED

            updated_referral = self._referral_repo.update_points_and_status(
                id=referral.id,
                added_points=points_earned,
                status=new_status
            )
            
            if not updated_referral:
                return None

            # db.session.query(User).filter_by(id=referral.referrer_id).update({
            #     User.reward_points: User.reward_points + points_earned
            # })
            user = self._user_repo.get_user_by_id(referral.referrer_id)
            if user.reward_points is None:
                user.reward_points = 0
            user.reward_points += points_earned
            update_user_dto = UpdateUserDTO(reward_points=user.reward_points)
            self._user_repo.update_user(referral.referrer_id, update_user_dto)
            
            log_dto = ActivityLogCreateDTO(
                action=Variables.REFERRAL_POINTS_EARNED_ACTION,
                user_id=referral.referrer_id,
                entity_type=Variables.ENTITY_TYPE_REFERRAL,
                entity_id=referral.id,
                before=referral,
                after=updated_referral,
                ip_address="system",
                user_agent="system",
            )
            
            self._log.log(log_dto)
            return RewardCalculationResultDTO(
                referral_id=updated_referral.id,
                referrer_id=referral.referrer_id,
                referred_id=referred_id,
                points_earned=points_earned,
                new_status=new_status.value if hasattr(new_status, 'value') else new_status
            )
        except Exception as e:
            logger.error(f"[ReferralService] calculate_and_reward_commission failed: {e}")
            raise

referral_service = ReferralService()
