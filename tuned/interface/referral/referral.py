import logging
from sqlalchemy.exc import SQLAlchemyError
from tuned.extensions import db
from tuned.repository import repositories
from tuned.services.referral_service import referral_service
from tuned.core.events import get_event_bus
from tuned.interface.audit import audit_service
from tuned.dtos.referral import ReferralResponseDTO

logger = logging.getLogger(__name__)

class ReferralInterface:
    def __init__(self) -> None: 
        self._user_repo = repositories.user
        self._referral_repo = repositories.referral

    def process_signup(self, new_user_id: str, referral_code: str) -> None:
        try:
            referral = referral_service.process_signup_with_referral(new_user_id, referral_code)
            if referral:
                db.session.commit()
                # TODO: Audit log or event for sign-up completion via referral
                audit_service.activity_log.create_system_log(#??
                    action="referral_signup",
                    details={"referrer_id": referral.referrer_id, "referred_id": new_user_id},
                    ip_address="system"
                )
        except Exception as e:
            db.session.rollback()
            logger.error(f"[ReferralInterface] Error in process_signup: {e}")

    def reward_referrer(self, referred_id: str, order_value: float) -> None:
        try:
            reward_data = referral_service.calculate_and_reward_commission(referred_id, order_value)
            if not reward_data:
                return

            referral_id = reward_data["referral_id"]
            referrer_id = reward_data["referrer_id"]
            commission_earned = reward_data["commission_earned"]
            new_status = reward_data["new_status"]

            updated_referral = self._referral_repo.update_commission_and_status(
                id=referral_id,
                added_commission=commission_earned,
                status=new_status
            )

            referrer = self._user_repo.get_user_by_id(referrer_id)
            if referrer:
                referrer.reward_points = referrer.reward_points + commission_earned
                db.session.flush()

            # 3. Audit Logging
            audit_service.activity_log.create_system_log(
                action="referral_commission_earned",
                details={#??
                    "referrer_id": referrer_id, 
                    "referred_id": referred_id, 
                    "commission": commission_earned
                },
                ip_address="system"
            )

            db.session.commit()

            payload = {
                "referrer_id": referrer_id,
                "referred_id": referred_id,
                "commission_earned": commission_earned,
                "new_total": referrer.reward_points if referrer else commission_earned,
                "referral": ReferralResponseDTO.from_model(updated_referral).to_dict() if updated_referral else None
            }
            get_event_bus().emit("ReferralCommissionEarned", payload)
            logger.info(f"[ReferralInterface] Successfully rewarded {commission_earned} points to user {referrer_id}")

        except Exception as e:
            db.session.rollback()
            logger.error(f"[ReferralInterface] Failed to reward referrer: {e}")
            raise
