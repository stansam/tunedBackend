import logging
from tuned.core.events import EventBus

logger = logging.getLogger(__name__)

class ReferralEventHandlers:
    def __init__(self, bus: EventBus) -> None:
        self.bus = bus

    def register(self) -> None:
        self.bus.on("PaymentCompleted", self.handle_payment_completed)
        self.bus.on("ReferralCommissionEarned", self.handle_commission_earned)
        logger.info("[ReferralEventHandlers] Registered.")

    def handle_payment_completed(self, payload: dict) -> None:
        """
        Triggered when a payment succeeds.Enqueue a background task
        to calculate and reward referral commission without slowing down checkout.
        Expected payload: {"payment_id": str, "user_id": str}
        """
        payment_id = payload.get("payment_id")
        user_id = payload.get("user_id")
        
        if payment_id and user_id:
            logger.info(f"[ReferralEventHandlers] PaymentCompleted event received for user {user_id}. Enqueueing referral check task.")
            from tuned.tasks.referral_tasks import process_referral_reward_task
            process_referral_reward_task.delay(payment_id, user_id)

    def handle_commission_earned(self, payload: dict) -> None:
        """
        Triggered when commission is successfully awarded.
        Emits a socket event to the referrer's room.
        """
        referrer_id = payload.get("referrer_id")
        commission = payload.get("commission_earned")
        logger.info(f"[ReferralEventHandlers] ReferralCommissionEarned for {referrer_id}: {commission}")
        
        try:
            from tuned.extensions import socketio
            room = f"user_{referrer_id}"
            socketio.emit('dashboard:points_updated', payload, room=room)
        except Exception as e:
            logger.error(f"[ReferralEventHandlers] Failed to emit socket event: {e}")
