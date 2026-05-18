from __future__ import annotations

import logging
from uuid import UUID
from decimal import Decimal
from typing import Optional

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from tuned.models import Order
from tuned.models.enums import OrderStatus
from tuned.dtos.order import OrderDraftCreateDTO
from tuned.core.exceptions import DatabaseError
from tuned.core.logging import get_logger

logger: logging.Logger = get_logger(__name__)

class UpsertDraftOrder:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, dto: OrderDraftCreateDTO) -> Order:
        try:
            stmt = select(Order).where(Order.client_id == dto.user_id, Order.status == OrderStatus.DRAFT)
            order = self.session.scalar(stmt)

            if not order:
                order = Order(
                    client_id=dto.user_id,
                    status=OrderStatus.DRAFT,
                    paid=False
                )
                self.session.add(order)

            if dto.service_id is not None: order.service_id = UUID(dto.service_id)
            if dto.academic_level_id is not None: order.academic_level_id = UUID(dto.academic_level_id)
            if dto.deadline_id is not None: order.deadline_id = UUID(dto.deadline_id)
            if dto.title is not None: order.title = dto.title
            if dto.instructions is not None: order.instructions = dto.instructions
            if dto.word_count is not None: order.word_count = dto.word_count
            if dto.page_count is not None: order.page_count = Decimal(str(dto.page_count))
            if dto.format_style is not None: order.format_style = dto.format_style
            if dto.sources is not None: order.sources = dto.sources
            if dto.line_spacing is not None: order.line_spacing = dto.line_spacing
            if dto.due_date is not None: order.due_date = dto.due_date
            if dto.report_type is not None: order.report_type = dto.report_type

            self.session.flush()
            return order
        except SQLAlchemyError as exc:
            logger.error("[UpsertDraftOrder] DB error: %s", exc)
            raise DatabaseError(str(exc)) from exc


class GetDraftOrder:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, user_id: str) -> Optional[Order]:
        try:
            stmt = select(Order).where(Order.client_id == user_id, Order.status == OrderStatus.DRAFT)
            return self.session.scalar(stmt)
        except SQLAlchemyError as exc:
            logger.error("[GetDraftOrder] DB error: %s", exc)
            raise DatabaseError(str(exc)) from exc
