from __future__ import annotations
import logging
from typing import Optional, TYPE_CHECKING
from tuned.core.logging import get_logger
from tuned.dtos.audit import ActivityLogCreateDTO
from tuned.dtos.order import (
    ReorderResponseDTO, CreateOrderRequestDTO, CreateOrderResponseDTO,
    ValidateDiscountRequestDTO, ValidateDiscountResponseDTO,
    OrderFileUploadResponseDTO, OrderDraftCreateDTO, OrderDraftResponseDTO
)
from tuned.dtos.user import UpdateUserDTO
from tuned.dtos.price import CalculatePriceRequestDTO
from tuned.repository.exceptions import DatabaseError, NotFound
from tuned.repository.protocols import OrderRepositoryProtocol
from tuned.models.enums import DiscountType

if TYPE_CHECKING:
    from tuned.interface import Services
    from tuned.repository import Repository
    from tuned.interface.protocols import ActivityLogServiceProtocol
    from tuned.interface.audit import AuditService
    from tuned.models import Order
    from werkzeug.datastructures import FileStorage

logger: logging.Logger = get_logger(__name__)


class OrderService:
    def __init__(
        self,
        repos: Repository,
        interfaces: Optional["Services"] = None,
        repo: Optional[OrderRepositoryProtocol] = None,
        audit_service: Optional[ActivityLogServiceProtocol] = None,
    ) -> None:
        self._repo: OrderRepositoryProtocol
        self._repos = repos
        self._interfaces = interfaces
        self._audit: Optional[AuditService] = None
        self._audit_service: ActivityLogServiceProtocol

        self._repo = repo or repos.order
        from tuned.interface.audit import AuditService as AuditAggregator
        self._audit = AuditAggregator(repos=repos)
        self._audit_service = audit_service or self._audit.activity_log

    def reorder(self, order_id: str, user_id: str) -> ReorderResponseDTO:
        try:
            source = self._repo.get_order_for_reorder(order_id, user_id)
            new_order = self._repo.create_reorder(source, user_id)

            try:
                self._audit_service.log(ActivityLogCreateDTO(
                    action=Variables.ORDER_REORDERED,
                    user_id=user_id,
                    entity_type="Order",
                    entity_id=str(new_order.id),
                    after=new_order,
                    created_by=user_id,
                    ip_address="system",
                    user_agent="system"
                ))
            except Exception as audit_exc:
                logger.error(
                    "[OrderService.reorder] Audit failed for new order %s: %r",
                    new_order.id, audit_exc,
                )

            try:
                from tuned.core.events import get_event_bus
                get_event_bus().emit("order.created", {
                    "order_id":     str(new_order.id),
                    "client_id":    user_id,
                    "order_number": new_order.order_number,
                })
            except Exception as event_exc:
                logger.error(
                    "[OrderService.reorder] Event emit failed for %s: %r",
                    new_order.id, event_exc,
                )

            self._repo.save()
            logger.info(
                "[OrderService.reorder] User %s reordered %s → new order %s",
                user_id, order_id, new_order.order_number,
            )
            return ReorderResponseDTO(
                order_id=str(new_order.id),
                order_number=new_order.order_number,
                redirect_url=f"/client/orders/{new_order.id}",
            )

        except NotFound:
            self._repo.rollback()
            logger.warning(
                "[OrderService.reorder] Order %s not found for user %s",
                order_id, user_id,
            )
            raise
        except DatabaseError:
            self._repo.rollback()
            logger.error(
                "[OrderService.reorder] DB error for order %s user %s",
                order_id, user_id,
            )
            raise
        except Exception:
            self._repo.rollback()
            raise

    def create_order(self, dto: CreateOrderRequestDTO, user_id: str, ip_address: str, user_agent: str) -> CreateOrderResponseDTO:
        try:
            # 1. Fetch user to check points balance
            user = self._repos.user.get_user_by_id(user_id)
            if dto.points_to_redeem > (user.reward_points or 0):
                raise ValueError("Insufficient reward points")

            # 2. Calculate price
            if not self._interfaces:
                raise RuntimeError("Services not injected")
            
            calc_request = CalculatePriceRequestDTO(
                service_id=dto.service_id,
                academic_level_id=dto.academic_level_id,
                deadline_id=dto.deadline_id,
                word_count=dto.word_count,
                page_count=dto.page_count,
                report_type=dto.report_type.value if dto.report_type else None,
                line_spacing=dto.line_spacing.value if dto.line_spacing else None,
            )
            price_resp = self._interfaces.price_rate.calculate_price(calc_request)
            
            subtotal = price_resp.total_price
            # TODO: Seperate discount and points redemption
            # 3. Validate and apply discount
            discount_amount = 0.0
            discount = None
            if dto.discount_code:
                val_resp = self.validate_discount(dto.discount_code, subtotal)
                if not val_resp.valid:
                    raise ValueError(f"Invalid discount: {val_resp.description}")
                discount_amount = val_resp.discount_amount
                discount = self._repo.get_discount_by_code(dto.discount_code)

            # 4. Check points value
            total_discount = discount_amount + dto.points_to_redeem
            total_price = max(subtotal - total_discount, 0.0)

            if dto.points_to_redeem > total_price + dto.points_to_redeem: # points value cannot exceed the remaining price
                raise ValueError("Points redemption value exceeds order total")

            # 5. Create Order
            order = self._repo.create_order(user_id, dto, total_price, subtotal)

            # 6. Link discount
            if discount:
                self._repo.link_discount_to_order(order, discount, discount_amount)

            # 7. Deduct points
            if dto.points_to_redeem > 0:
                new_balance = (user.reward_points or 0) - dto.points_to_redeem
                update_dto = UpdateUserDTO(reward_points=new_balance)
                self._repos.user.update_user(update_dto, actor_id=user_id)

            # 8. Audit log
            try:
                self._audit_service.log(ActivityLogCreateDTO(
                    action=Variables.ORDER_CREATED,
                    user_id=user_id,
                    entity_type="Order",
                    entity_id=str(order.id),
                    created_by=user_id,
                    ip_address=ip_address,
                    user_agent=user_agent
                ))
            except Exception as audit_exc:
                logger.error("[OrderService.create_order] Audit failed: %r", audit_exc)

            # 9. Emit event
            try:
                from tuned.core.events import get_event_bus
                get_event_bus().emit("order.created", {
                    "order_id": str(order.id),
                    "client_id": user_id,
                    "order_number": order.order_number,
                })
            except Exception as event_exc:
                logger.error("[OrderService.create_order] Event emit failed: %r", event_exc)

            # 10. Schedule Reminder
            try:
                from tuned.tasks.order_tasks import send_payment_reminder
                send_payment_reminder.apply_async(args=[str(order.id)], countdown=3600)
            except Exception as task_exc:
                logger.error("[OrderService.create_order] Celery task failed: %r", task_exc)

            self._repo.save()
            return CreateOrderResponseDTO(
                order_id=str(order.id),
                order_number=order.order_number,
                success=True,
                message="Order created successfully"
            )

        except ValueError as e:
            self._repo.rollback()
            raise e
        except Exception as e:
            self._repo.rollback()
            logger.error("[OrderService.create_order] Failed: %r", e)
            raise DatabaseError("Failed to create order") from e

    def validate_discount(self, code: str, subtotal: float) -> ValidateDiscountResponseDTO:
        discount = self._repo.get_discount_by_code(code)
        if not discount or not discount.is_active:
            return ValidateDiscountResponseDTO(valid=False, discount_amount=0.0, description="Invalid or expired discount code")
        
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)

        if discount.valid_from and now < discount.valid_from.replace(tzinfo=timezone.utc):
            return ValidateDiscountResponseDTO(valid=False, discount_amount=0.0, description="Discount code is not yet active")
        
        if discount.valid_to and now > discount.valid_to.replace(tzinfo=timezone.utc):
            return ValidateDiscountResponseDTO(valid=False, discount_amount=0.0, description="Discount code has expired")

        if discount.usage_limit and (discount.times_used or 0) >= discount.usage_limit:
            return ValidateDiscountResponseDTO(valid=False, discount_amount=0.0, description="Discount code usage limit reached")

        if discount.min_order_value and subtotal < discount.min_order_value:
            return ValidateDiscountResponseDTO(valid=False, discount_amount=0.0, description=f"Minimum order value of ${discount.min_order_value} required")

        amount = 0.0
        if discount.discount_type == DiscountType.PERCENTAGE:
            amount = (subtotal * discount.amount) / 100.0
            if discount.max_discount_value:
                amount = min(amount, discount.max_discount_value)
        else:
            amount = min(discount.amount, subtotal)

        return ValidateDiscountResponseDTO(valid=True, discount_amount=amount, description=discount.description)

    def upload_order_files(self, order_id: str, user_id: str, files: list[FileStorage], ip_address: str, user_agent: str) -> OrderFileUploadResponseDTO:
        try:
            order = self._repo.get_order_by_id_for_client(order_id, user_id)
            import os, uuid
            from flask import current_app

            upload_dir = os.path.join(current_app.root_path, 'static', 'client', 'assets', 'order_files', order_id)
            os.makedirs(upload_dir, exist_ok=True)

            file_ids = []
            for file in files:
                ext = os.path.splitext(file.filename)[1] if file.filename else ''
                filename = f"{uuid.uuid4()}{ext}"
                file_path = os.path.join(upload_dir, filename)
                file.save(file_path)

                relative_path = f"/static/client/assets/order_files/{order_id}/{filename}"
                order_file = self._repo.create_order_file(order_id, file.filename or filename, relative_path)
                file_ids.append(str(order_file.id))

            try:
                self._audit_service.log(ActivityLogCreateDTO(
                    action=Variables.ORDER_FILES_UPLOADED,
                    user_id=user_id,
                    entity_type=Variables.ENTITY_TYPE_ORDER,
                    entity_id=order_id,
                    created_by=user_id,
                    ip_address=ip_address,
                    user_agent=user_agent
                ))
            except Exception as audit_exc:
                logger.error("[OrderService.upload_order_files] Audit failed: %r", audit_exc)

            self._repo.save()
            return OrderFileUploadResponseDTO(uploaded_count=len(file_ids), file_ids=file_ids)
        except Exception as e:
            self._repo.rollback()
            logger.error("[OrderService.upload_order_files] Failed: %r", e)
            raise e

    def save_draft(self, dto: OrderDraftCreateDTO) -> OrderDraftResponseDTO:
        try:
            draft = self._repo.upsert_draft(dto)

            # Emit event
            try:
                from tuned.core.events import get_event_bus
                get_event_bus().emit("order.draft_saved", {
                    "user_id": dto.user_id,
                    "order_id": str(draft.id),
                })
            except Exception as event_exc:
                logger.error("[OrderService.save_draft] Event emit failed: %r", event_exc)

            # Schedule Reminder
            try:
                from tuned.tasks.order_tasks import schedule_draft_reminder
                schedule_draft_reminder.apply_async(args=[str(draft.id)], countdown=86400)
            except Exception as task_exc:
                logger.error("[OrderService.save_draft] Celery task failed: %r", task_exc)

            self._repo.save()
            return OrderDraftResponseDTO.from_model(draft)
        except Exception as e:
            self._repo.rollback()
            logger.error("[OrderService.save_draft] Failed: %r", e)
            raise DatabaseError("Failed to save draft") from e

    def get_draft(self, user_id: str) -> Optional[OrderDraftResponseDTO]:
        try:
            draft = self._repo.get_draft(user_id)
            if not draft:
                return None
            return OrderDraftResponseDTO.from_model(draft)
        except Exception as e:
            logger.error("[OrderService.get_draft] Failed: %r", e)
            raise DatabaseError("Failed to fetch draft") from e
