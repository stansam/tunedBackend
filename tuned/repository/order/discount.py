from __future__ import annotations

import logging
from decimal import Decimal
from typing import Optional

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from tuned.models import Order
from tuned.models.payment import Discount
from tuned.core.exceptions import DatabaseError
from tuned.core.logging import get_logger

logger: logging.Logger = get_logger(__name__)

class LinkDiscountToOrder:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, order: Order, discount: Discount, amount: float) -> None:
        try:
            order.discounts.append(discount)
            order.discount_amount = Decimal(str(amount))
            discount.times_used += 1
            self.session.flush()
        except SQLAlchemyError as exc:
            logger.error("[LinkDiscountToOrder] DB error: %s", exc)
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
