from __future__ import annotations
import logging
from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from tuned.models.order_delivery import OrderDelivery, OrderDeliveryFile
from tuned.core.exceptions import DatabaseError, NotFound
from tuned.core.logging import get_logger
from tuned.dtos.order_delivery import (
    AddDeliveryFilesDTO,
    OrderDeliveryResponseDTO,
)

logger: logging.Logger = get_logger(__name__)

class AddFilesToDelivery:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, delivery_id: str, data: AddDeliveryFilesDTO) -> OrderDelivery:
        try:
            stmt = select(OrderDelivery).where(
                OrderDelivery.id == UUID(delivery_id),
                OrderDelivery.is_deleted == False
            )
            delivery = self.session.scalar(stmt)
            if not delivery:
                raise NotFound(f"OrderDelivery {delivery_id} not found")

            for file_dto in data.delivery_files:
                delivery_file = OrderDeliveryFile(
                    delivery_id=delivery.id,
                    filename=file_dto.filename,
                    original_filename=file_dto.original_filename,
                    file_path=file_dto.file_path,
                    file_type=file_dto.file_type,
                    file_format=file_dto.file_format,
                    description=file_dto.description,
                )
                self.session.add(delivery_file)

            delivery.updated_at = datetime.now(timezone.utc)
            self.session.flush()

            self.session.refresh(delivery, ["delivery_files"])
            return delivery
        except NotFound:
            raise
        except SQLAlchemyError as exc:
            logger.error("[AddFilesToDelivery] DB error: %s", exc)
            raise DatabaseError(str(exc)) from exc