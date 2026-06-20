from __future__ import annotations

import logging
from celery import Task
from celery.utils.log import get_task_logger
from tuned.celery_app import celery_app

logger = get_task_logger(__name__)

@celery_app.task(
    name="tuned.tasks.referral_tasks.process_referral_reward_task",
    bind=True,
    queue="notifications",
    max_retries=2,
    acks_late=True,
)
def process_referral_reward_task(self: Task, payment_id: str, user_id: str) -> None:
    try:
        logger.info(
            "[ReferralTasks] Processing referral reward for payment %s, user %s",
            payment_id, user_id
        )
        from tuned.utils.dependencies import get_services
        payment = get_services().payment.payment.get_details(payment_id)
        if not payment:
            logger.warning("[ReferralTasks] Payment %s not found. Cannot award referral.", payment_id)
            return
        
        order_value = payment.amount
        get_services().referral.reward_referrer(
            referred_id=user_id,
            order_value=float(order_value)
        )
        logger.info("[ReferralTasks] Successfully completed referral reward processing for user %s", user_id)
        
    except Exception as exc:
        logger.error("[ReferralTasks] Error processing referral reward for payment %s: %r", payment_id, exc, exc_info=True)
        raise self.retry(exc=exc, countdown=120)
