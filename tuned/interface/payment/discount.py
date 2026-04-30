from __future__ import annotations
import logging
from typing import Optional, TYPE_CHECKING
from tuned.core.logging import get_logger
from tuned.dtos.audit import ActivityLogCreateDTO
from tuned.dtos.payment import DiscountCreateDTO, DiscountResponseDTO
from tuned.utils.variables import Variables

if TYPE_CHECKING:
    from tuned.repository import Repository

logger: logging.Logger = get_logger(__name__)

class ApplyDiscount:
    def __init__(self, repos: Optional[Repository] = None) -> None:
        if repos:
            self._repo = repos.payment.discount
            from tuned.interface.audit import AuditService
            self._audit = AuditService(repos=repos)
        else:
            from tuned.repository import repositories
            self._repo = repositories.payment.discount
            from tuned.interface.audit import audit_service
            self._audit = audit_service

    def execute(self, code: str, order_value: float, user_id: str) -> DiscountResponseDTO:
        try:
            discount = self._repo.get_by_code(code)
            
            if not discount.is_active:
                raise ValueError("Discount code is not active.")
            if discount.usage_limit and discount.times_used >= discount.usage_limit:
                raise ValueError("Discount usage limit exceeded.")
            if discount.min_order_value and order_value < discount.min_order_value:
                raise ValueError(f"Order value must be at least {discount.min_order_value} to use this discount.")
                
            updated_discount = self._repo.increment_usage(discount.id)

            try:
                self._audit.activity_log.log(ActivityLogCreateDTO(
                    action=Variables.DISCOUNT_APPLY_ACTION,
                    user_id=user_id,
                    entity_type=Variables.DISCOUNT_ENTITY_TYPE,
                    entity_id=discount.id,
                    before=discount,
                    after=updated_discount,
                    created_by=user_id,
                    ip_address="system",
                    user_agent="system"
                ))
                logger.info(f"[ApplyDiscount] Audit successfully applied for discount {code}")
            except Exception as audit_exc:
                logger.error(f"[ApplyDiscount] Audit failed for discount {code}: {audit_exc!r}")

            logger.info(f"[ApplyDiscount] Discount {code} successfully applied")
            return updated_discount
        except Exception as exc:
            logger.error(f"[ApplyDiscount] Failed to apply discount {code}: {exc!r}")
            raise

class CreateDiscount:
    def __init__(self, repos: Optional[Repository] = None) -> None:
        if repos:
            self._repo = repos.payment.discount
            from tuned.interface.audit import AuditService
            self._audit = AuditService(repos=repos)
        else:
            from tuned.repository import repositories
            self._repo = repositories.payment.discount
            from tuned.interface.audit import audit_service
            self._audit = audit_service

    def execute(self, data: DiscountCreateDTO, actor_id: str) -> DiscountResponseDTO:
        try:
            discount = self._repo.create(data)

            try:
                self._audit.activity_log.log(ActivityLogCreateDTO(
                    action=Variables.DISCOUNT_CREATE_ACTION,
                    user_id=actor_id, # admin id
                    entity_type=Variables.DISCOUNT_ENTITY_TYPE,
                    entity_id=discount.id,
                    after=discount,
                    created_by=actor_id,
                    ip_address="system",
                    user_agent="system"
                ))
                logger.info(f"[CreateDiscount] Audit successfully applied for discount {discount.code}")
            except Exception as audit_exc:
                logger.error(f"[CreateDiscount] Audit failed for discount {discount.code}: {audit_exc!r}")

            logger.info(f"[CreateDiscount] Discount {discount.code} created by {actor_id}")
            return discount
        except Exception as exc:
            logger.error(f"[CreateDiscount] Failed to create discount: {exc!r}")
            raise

class GetDiscountDetails:
    def __init__(self, repos: Optional[Repository] = None) -> None:
        if repos:
            self._repo = repos.payment.discount
        else:
            from tuned.repository import repositories
            self._repo = repositories.payment.discount

    def execute(self, discount_id: str) -> DiscountResponseDTO:
        try:
            return self._repo.get_by_id(discount_id)
        except Exception as exc:
            logger.error(f"[GetDiscountDetails] Failed to get discount {discount_id}: {exc!r}")
            raise
