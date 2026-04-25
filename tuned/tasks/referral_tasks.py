import logging
from celery import shared_task
from tuned.interface import referral as referral_interface
from tuned.interface.payment import payment_service

logger = logging.getLogger(__name__)

@shared_task(name="referral_tasks.process_referral_reward_task")
def process_referral_reward_task(payment_id: str, user_id: str) -> None:
    try:
        logger.info(f"[ReferralTasks] Processing referral reward for payment {payment_id}, user {user_id}")

        payment = payment_service.payment.get_details(payment_id)
        if not payment:
            logger.warning(f"[ReferralTasks] Payment {payment_id} not found. Cannot award referral.")
            return
        
        order_value = payment.amount
        referral_interface.reward_referrer(
            referred_id=user_id,
            order_value=order_value
        )
        logger.info(f"[ReferralTasks] Successfully completed referral reward processing for user {user_id}")
        
    except Exception as exc:
        logger.error(f"[ReferralTasks] Error processing referral reward for payment {payment_id}: {exc!r}", exc_info=True)
