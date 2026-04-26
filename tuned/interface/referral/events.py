import logging
from tuned.core.events import EventBus

logger = logging.getLogger(__name__)

class ReferralEventHandlers:
    def __init__(self, bus: EventBus) -> None:
        self.bus = bus

    def register(self) -> None:
        self.bus.on("PaymentCompleted", self.handle_payment_completed)
        self.bus.on("ReferralCommissionEarned", self.handle_commission_earned)
        self.bus.on("user.registered_with_referral", self.handle_user_registered_with_referral)
        logger.info("[ReferralEventHandlers] Registered.")

    def handle_user_registered_with_referral(self, payload: dict) -> None:
        new_user_id = payload.get("new_user_id")
        referral_code = payload.get("referral_code")
        
        if new_user_id and referral_code:
            logger.info(f"[ReferralEventHandlers] Processing referral for new user {new_user_id} with code {referral_code}")
            try:
                from tuned.interface import referral as referral_interface
                referral_interface.process_signup(new_user_id, referral_code)
            except Exception as e:
                logger.error(f"[ReferralEventHandlers] Failed to process referral signup: {e}")

    def handle_payment_completed(self, payload: dict) -> None:
        payment_id = payload.get("payment_id")
        user_id = payload.get("user_id")
        
        if payment_id and user_id:
            logger.info(f"[ReferralEventHandlers] PaymentCompleted event received for user {user_id}. Enqueueing referral check task.")
            from tuned.tasks.referral_tasks import process_referral_reward_task
            process_referral_reward_task.delay(payment_id, user_id)

    def handle_commission_earned(self, payload: dict) -> None:
        referrer_id = payload.get("referrer_id")
        commission = payload.get("commission_earned")
        logger.info(f"[ReferralEventHandlers] ReferralCommissionEarned for {referrer_id}: {commission}")
        
        try:
            from tuned.extensions import socketio
            from tuned.tasks.notifications import create_in_app_notification
            from tuned.models.enums import NotificationType
            room = f"user_{referrer_id}"
            socketio.emit('dashboard:points_updated', payload, room=room)
            create_in_app_notification.delay(
                user_id=referrer_id,
                title="Referral Points Earned!",
                message=f"Congratulations! You just earned {payload.get('commission_earned')} reward points from a successful referral.",
                notification_type=NotificationType.SUCCESS,
                action_url='/dashboard/referrals'
            )
        except Exception as e:
            logger.error(f"[ReferralEventHandlers] Failed to emit socket event: {e}")
