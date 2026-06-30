from __future__ import annotations
import logging
from uuid import UUID
from typing import Sequence
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

from tuned.models.order_delivery import OrderDelivery, OrderDeliveryFile
from tuned.models.enums import DeliveryStatus
from tuned.core.exceptions import DatabaseError, NotFound
from tuned.core.logging import get_logger
from tuned.dtos.order_delivery import (
    CreateOrderDeliveryDTO,
    UpdateOrderDeliveryStatusDTO,
)

logger: logging.Logger = get_logger(__name__)

class CreateOrderDelivery:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, data: CreateOrderDeliveryDTO) -> OrderDelivery:
        try:
            delivery = OrderDelivery(
                id=UUID(data.id) if data.id else None,
                order_id=UUID(data.order_id),
                delivery_status=DeliveryStatus.DELIVERED,
                client_notified=False,
            )
            self.session.add(delivery)
            self.session.flush()

            for file_dto in data.delivery_files:
                delivery_file = OrderDeliveryFile(
                    delivery_id=delivery.id,
                    asset_id=UUID(file_dto.asset_id) if file_dto.asset_id else None,
                    filename=file_dto.filename,
                    original_filename=file_dto.original_filename,
                    file_path=file_dto.file_path,
                    file_size=file_dto.file_size,
                    file_type=file_dto.file_type,
                    file_format=file_dto.file_format,
                    description=file_dto.description,
                )
                self.session.add(delivery_file)

            self.session.flush()
            self.session.refresh(delivery, ["delivery_files"])

            return delivery
        except SQLAlchemyError as exc:
            logger.error("[CreateOrderDelivery] DB error: %s", exc)
            raise DatabaseError(str(exc)) from exc


class GetOrderDeliveries:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, order_id: str) -> Sequence[OrderDelivery]:
        try:
            stmt = (
                select(OrderDelivery)
                .options(joinedload(OrderDelivery.delivery_files))
                .where(
                    OrderDelivery.order_id == UUID(order_id),
                    OrderDelivery.is_deleted == False
                )
                .order_by(OrderDelivery.created_at.desc())
            )
            deliveries = self.session.scalars(stmt).unique().all()
            return deliveries
        except SQLAlchemyError as exc:
            logger.error("[GetOrderDeliveries] DB error: %s", exc)
            raise DatabaseError(str(exc)) from exc


class GetOrderDeliveryByID:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, delivery_id: str) -> OrderDelivery:
        try:
            stmt = (
                select(OrderDelivery)
                .options(joinedload(OrderDelivery.delivery_files))
                .where(
                    OrderDelivery.id == UUID(delivery_id),
                    OrderDelivery.is_deleted == False
                )
            )
            delivery = self.session.scalars(stmt).unique().first()
            if not delivery:
                raise NotFound(f"OrderDelivery {delivery_id} not found")

            return delivery
        except NotFound:
            raise
        except SQLAlchemyError as exc:
            logger.error("[GetOrderDeliveryByID] DB error: %s", exc)
            raise DatabaseError(str(exc)) from exc

class UpdateDeliveryStatus:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, delivery_id: str, data: UpdateOrderDeliveryStatusDTO) -> OrderDelivery:
        try:
            stmt = select(OrderDelivery).where(
                OrderDelivery.id == UUID(delivery_id),
                OrderDelivery.is_deleted == False
            )
            delivery = self.session.scalar(stmt)
            if not delivery:
                raise NotFound(f"OrderDelivery {delivery_id} not found")

            delivery.delivery_status = data.delivery_status

            if data.delivery_status == DeliveryStatus.DELIVERED:
                delivery.delivered_at = datetime.now(timezone.utc)

            delivery.updated_at = datetime.now(timezone.utc)
            
            self.session.flush()
            self.session.refresh(delivery, ["delivery_files"])

            return delivery
        except NotFound:
            raise
        except SQLAlchemyError as exc:
            logger.error("[UpdateDeliveryStatus] DB error: %s", exc)
            raise DatabaseError(str(exc)) from exc


class MarkDeliveryClientNotified:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, delivery_id: str) -> OrderDelivery:
        try:
            stmt = select(OrderDelivery).where(
                OrderDelivery.id == UUID(delivery_id),
                OrderDelivery.is_deleted == False
            )
            delivery = self.session.scalar(stmt)
            if not delivery:
                raise NotFound(f"OrderDelivery {delivery_id} not found")

            delivery.client_notified = True
            delivery.client_notified_at = datetime.now(timezone.utc)
            delivery.updated_at = datetime.now(timezone.utc)
            self.session.flush()

            self.session.refresh(delivery, ["delivery_files"])
            return delivery
        except NotFound:
            raise
        except SQLAlchemyError as exc:
            logger.error("[MarkDeliveryClientNotified] DB error: %s", exc)
            raise DatabaseError(str(exc)) from exc

class DeleteOrderDelivery:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, delivery_id: str, user_id: str) -> None:
        try:
            stmt = select(OrderDelivery).where(
                OrderDelivery.id == UUID(delivery_id),
                OrderDelivery.is_deleted == False
            )
            delivery = self.session.scalar(stmt)
            if not delivery:
                raise NotFound(f"OrderDelivery {delivery_id} not found")

            delivery.is_deleted = True
            delivery.deleted_at = datetime.now(timezone.utc)
            delivery.deleted_by = UUID(user_id) if user_id else None

            for file in delivery.delivery_files:
                file.is_deleted = True
                file.deleted_at = datetime.now(timezone.utc)
                file.deleted_by = UUID(user_id) if user_id else None

            self.session.flush()
        except NotFound:
            raise
        except SQLAlchemyError as exc:
            logger.error("[DeleteOrderDelivery] DB error: %s", exc)
            raise DatabaseError(str(exc)) from exc
