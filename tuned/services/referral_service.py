from datetime import datetime, timezone, timedelta
from dataclasses import asdict
import logging
from typing import Optional, TYPE_CHECKING
from tuned.models.enums import ReferralStatus
from tuned.dtos import (
    ReferralResponseDTO,
    RewardCalculationResultDTO,
    ActivityLogCreateDTO,
    UpdateUserDTO,
    ReferralRedemptionResultDTO,
)
from tuned.core.logging import get_logger
from tuned.repository.exceptions import DatabaseError, NotFound
from tuned.repository.protocols import (
    OrderRepositoryProtocol,
    ReferralRepositoryProtocol,
    UserRepositoryProtocol,
)
from tuned.utils.variables import Variables

if TYPE_CHECKING:
    from tuned.interface.protocols import ActivityLogServiceProtocol

logger: logging.Logger = get_logger(__name__)

class ReferralService:
    def __init__(
        self,
        user_repo: UserRepositoryProtocol,
        referral_repo: ReferralRepositoryProtocol,
        order_repo: OrderRepositoryProtocol,
        audit_service: "ActivityLogServiceProtocol",
    ) -> None:
        self._user_repo = user_repo
        self._referral_repo = referral_repo
        self._order_repo = order_repo
        self._audit_service = audit_service

    def _rollback_all(self) -> None:
        self._order_repo.rollback()
        self._referral_repo.rollback()
        self._user_repo.rollback()

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
                after=asdict(referral),
                ip_address="system",
                user_agent="system"
            )
            self._audit_service.log(log_dto)
            self._referral_repo.save()
            logger.info(f"[ReferralService] Created PENDING referral {referral.id} for referrer {referrer_id}")
            return referral
        except (DatabaseError, NotFound, ValueError):
            self._rollback_all()
            raise
        except Exception as e:
            self._rollback_all()
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

            paid_orders = self._order_repo.get_paid_order_count(referred_id)
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
                before=asdict(referral),
                after=asdict(updated_referral),
                ip_address="system",
                user_agent="system",
                created_by=referral.referrer_id,
            )
            
            self._audit_service.log(log_dto)
            self._referral_repo.save()
            return RewardCalculationResultDTO(
                referral_id=updated_referral.id,
                referrer_id=referral.referrer_id,
                referred_id=referred_id,
                points_earned=points_earned,
                new_status=new_status.value if hasattr(new_status, 'value') else str(new_status)
            )
        except (DatabaseError, NotFound, ValueError):
            self._rollback_all()
            raise
        except Exception as e:
            self._rollback_all()
            logger.error(f"[ReferralService] calculate_and_reward_commission failed: {e}")
            raise

    def redeem_points(
        self,
        user_id: str,
        order_id: str,
        points_to_redeem: int,
    ) -> ReferralRedemptionResultDTO:
        try:
            user = self._user_repo.get_user_by_id(user_id)
            if not user or (user.reward_points or 0) < points_to_redeem:
                logger.error(f"[ReferralService] Insufficient reward points for user {user_id}")
                raise ValueError("Insufficient reward points")

            if points_to_redeem <= 0:
                raise ValueError("Points to redeem must be greater than zero")

            order = self._order_repo.get_order_by_id_for_client(order_id, user_id)
            existing_discount_amount = order.discount_amount or 0.0
            existing_total_price = order.total_price
                
            if order.paid:
                logger.error(f"[ReferralService] Order {order_id} is already paid")
                raise ValueError("Cannot apply discount to a paid order")
                
            max_redeemable = int(order.total_price)
            if max_redeemable <= 0:
                raise ValueError("Order is not eligible for reward redemption")

            points_to_apply = min(points_to_redeem, max_redeemable)
                
            discount_amount = float(points_to_apply)
            
            new_balance = (user.reward_points or 0) - points_to_apply
            update_user_dto = UpdateUserDTO(
                user_id=user_id,
                reward_points=new_balance
            )
            self._user_repo.update_user(update_user_dto, actor_id=user_id)
            updated_order = self._order_repo.apply_discount(order_id, user_id, discount_amount)
            self._order_repo.save()
            
            log_dto = ActivityLogCreateDTO(
                action=Variables.REFERRAL_POINTS_REDEEMED_ACTION,
                user_id=user_id,
                entity_type=Variables.ORDER_ENTITY_TYPE,
                entity_id=order_id,
                before={
                    "discount_amount": existing_discount_amount,
                    "total_price": existing_total_price,
                },
                after={
                    "discount_amount": updated_order.discount_amount or 0.0,
                    "total_price": updated_order.total_price,
                },
                ip_address="system",
                user_agent="system",
                created_by=user_id,
            )
            self._audit_service.log(log_dto)            
            return ReferralRedemptionResultDTO(
                redeemed_points=points_to_apply,
                discount_amount=discount_amount,
                new_balance=new_balance,
                order_id=order_id,
                updated_total_price=updated_order.total_price,
            )
        except (DatabaseError, NotFound, ValueError):
            self._rollback_all()
            raise
        except Exception as e:
            self._rollback_all()
            logger.error(f"[ReferralService] redeem_points failed: {e}")
            raise
