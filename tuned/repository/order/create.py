from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from tuned.models import Order, OrderFile
from tuned.models.payment import Discount
from tuned.models.enums import OrderStatus
from tuned.dtos.order import CreateOrderRequestDTO, OrderDraftCreateDTO
from tuned.repository.exceptions import DatabaseError
from tuned.core.logging import get_logger

logger: logging.Logger = get_logger(__name__)


class CreateOrder:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, client_id: str, dto: CreateOrderRequestDTO, total_price: float, subtotal: float) -> Order:
        try:
            new_order = Order(
                client_id=client_id,
                service_id=dto.service_id,
                academic_level_id=dto.level_id,
                deadline_id=dto.deadline_id,
                title=dto.title,
                instructions=dto.instructions,
                word_count=dto.word_count,
                page_count=dto.page_count,
                format_style=dto.format_style,
                sources=dto.sources,
                line_spacing=dto.line_spacing,
                due_date=dto.due_date,
                report_type=dto.report_type,
                total_price=total_price,
                subtotal=subtotal,
                price_per_page=subtotal / dto.page_count if dto.page_count else 0,
                status=OrderStatus.PENDING,
                paid=False,
            )
            self.session.add(new_order)
            self.session.flush()
            return new_order
        except SQLAlchemyError as exc:
            logger.error("[CreateOrder] DB error: %s", exc)
            raise DatabaseError(str(exc)) from exc


class LinkDiscountToOrder:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, order: Order, discount: Discount, amount: float) -> None:
        try:
            order.discounts.append(discount)
            order.discount_amount = amount
            discount.times_used += 1
            self.session.flush()
        except SQLAlchemyError as exc:
            logger.error("[LinkDiscountToOrder] DB error: %s", exc)
            raise DatabaseError(str(exc)) from exc


class CreateOrderFile:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, order_id: str, filename: str, file_path: str) -> OrderFile:
        try:
            order_file = OrderFile(
                order_id=order_id,
                filename=filename,
                file_path=file_path,
                is_from_client=True
            )
            self.session.add(order_file)
            self.session.flush()
            return order_file
        except SQLAlchemyError as exc:
            logger.error("[CreateOrderFile] DB error: %s", exc)
            raise DatabaseError(str(exc)) from exc


class GetDiscountByCode:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, code: str) -> Optional[Discount]:
        try:
            stmt = select(Discount).where(Discount.code == code, Discount.is_active == True)
            return self.session.scalar(stmt)
        except SQLAlchemyError as exc:
            logger.error("[GetDiscountByCode] DB error: %s", exc)
            raise DatabaseError(str(exc)) from exc


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

            if dto.service_id is not None: order.service_id = dto.service_id
            if dto.academic_level_id is not None: order.academic_level_id = dto.academic_level_id
            if dto.deadline_id is not None: order.deadline_id = dto.deadline_id
            if dto.title is not None: order.title = dto.title
            if dto.instructions is not None: order.instructions = dto.instructions
            if dto.word_count is not None: order.word_count = dto.word_count
            if dto.page_count is not None: order.page_count = dto.page_count
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

class CreateOrderFromReorder:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, source: Order, client_id: str) -> Order:
        try:
            new_order = Order(
                client_id=client_id,
                service_id=source.service_id,
                academic_level_id=source.academic_level_id,
                deadline_id=source.deadline_id,
                title=source.title,
                instructions=source.instructions,
                word_count=source.word_count,
                page_count=source.page_count,
                format_style=source.format_style,
                sources=source.sources,
                line_spacing=source.line_spacing,
                report_type=source.report_type,
                due_date=source.due_date,
                total_price=source.total_price,
                price_per_page=source.price_per_page,
                subtotal=source.subtotal,
                discount_amount=source.discount_amount or 0,
                status=OrderStatus.PENDING,
                paid=False,
            )
            self.session.add(new_order)
            self.session.flush()
            return new_order
        except SQLAlchemyError as exc:
            logger.error("[CreateOrderFromReorder] DB error: %s", exc)
            raise DatabaseError(str(exc)) from exc
