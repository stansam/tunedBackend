from datetime import datetime, timezone, timedelta
import logging
from typing import Optional
from tuned.models.enums import ReferralStatus
from tuned.models import Order
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
                
            if order_value < 40.0:
                logger.debug(f"[ReferralService] Order value {order_value} is below the $40 minimum.")
                return None

            paid_orders = repositories.order.get_paid_order_count(referred_id)
            if paid_orders > 1:
                logger.debug(f"[ReferralService] Client {referred_id} has {paid_orders} paid orders. Referral reward only applies to the first order.")
                return None

            now = datetime.now(timezone.utc)
            monthly_count = self._referral_repo.count_monthly_completed_referrals(referral.referrer_id, now.year, now.month)
            
            if monthly_count == 0:
                points_earned = 10
            elif monthly_count in [1, 2, 3]:
                points_earned = 12
            else:
                points_earned = 15
            
            new_status = ReferralStatus.COMPLETED

            updated_referral = self._referral_repo.update_points_and_status(
                id=referral.id,
                added_points=points_earned,
                status=new_status,
                completed_at=now,
                expires_at=now + timedelta(days=90)
            )
            
            if not updated_referral:
                return None

            user = self._user_repo.get_user_by_id(referral.referrer_id)
            if user.reward_points is None:
                user.reward_points = 0
            user.reward_points += points_earned
            update_user_dto = UpdateUserDTO(
                user_id=str(user.id),
                reward_points=user.reward_points
            )
            self._user_repo.update_user(update_user_dto, actor_id=referral.referrer_id)
            
            log_dto = ActivityLogCreateDTO(
                action=Variables.REFERRAL_POINTS_EARNED_ACTION,
                user_id=referral.referrer_id,
                entity_type=Variables.ENTITY_TYPE_REFERRAL,
                entity_id=referral.id,
                before=referral,
                after=updated_referral,
                ip_address="system",
                user_agent="system",
                created_by=referral.referrer_id,
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

    def redeem_points(self, user_id: str, order_id: str, points_to_redeem: int) -> dict:
        try:
            user = self._user_repo.get_user_by_id(user_id)
            if not user or (user.reward_points or 0) < points_to_redeem:
                logger.error(f"[ReferralService] Insufficient reward points for user {user_id}")
                raise ValueError("Insufficient reward points")
            
            order = repositories.order.session.query(Order).get(order_id) #TODO: Update after implementing order repository and interface properly
            if not order or str(order.client_id) != user_id:
                logger.error(f"[ReferralService] Invalid order {order_id} for user {user_id}")
                raise ValueError("Order not found or access denied")

            existing_order = order 
                
            if order.paid:
                logger.error(f"[ReferralService] Order {order_id} is already paid")
                raise ValueError("Cannot apply discount to a paid order")
                
            max_redeemable = int(order.total_price) 
            if points_to_redeem > max_redeemable:
                points_to_redeem = max_redeemable
                
            discount_amount = float(points_to_redeem)
            
            new_balance = user.reward_points - points_to_redeem
            update_user_dto = UpdateUserDTO(
                user_id=user_id,
                reward_points=new_balance
            )
            self._user_repo.update_user(update_user_dto, actor_id=user_id)
            
            order.discount_amount = (order.discount_amount or 0.0) + discount_amount
            if hasattr(order, 'subtotal') and order.subtotal:
                order.total_price = order.subtotal - order.discount_amount
            else:
                order.total_price = order.total_price - discount_amount
            try: # TODO: Update after implementing order repository and interface properly
                repositories.order.session.flush()
                repositories.order.session.commit()
                repositories.order.session.refresh(order)
            except Exception as e:
                repositories.order.session.rollback()
                logger.error(f"[ReferralService] redeem_points failed: {e}")
                raise ValueError("Database error when trying to update order")
            
            log_dto = ActivityLogCreateDTO(
                action=Variables.REFERRAL_POINTS_REDEEMED_ACTION,
                user_id=user_id,
                entity_type=Variables.ORDER_ENTITY_TYPE,
                entity_id=order_id,
                before=existing_order,
                after=order,
                ip_address="system",
                user_agent="system",
                created_by=user_id,
            )
            self._log.log(log_dto)
            
            return {
                "redeemed_points": points_to_redeem,
                "discount_amount": discount_amount,
                "new_balance": new_balance
            }
        except Exception as e:
            logger.error(f"[ReferralService] redeem_points failed: {e}")
            raise

referral_service = ReferralService()
