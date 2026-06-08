from __future__ import annotations

import logging
import uuid

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from sqlalchemy import select

from tuned.models import OrderFile
from tuned.core.exceptions import DatabaseError, NotFound
from tuned.core.logging import get_logger
from tuned.dtos import CreateOrderFileDTO

logger: logging.Logger = get_logger(__name__)


class CreateOrderFile:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, order_id: str, req: CreateOrderFileDTO) -> OrderFile:
        try:
            order_file = OrderFile(
                order_id=order_id,
                asset_id=uuid.UUID(req.asset_id) if req.asset_id else None,
                filename=req.filename,
                file_path=req.file_path,
                file_size=req.file_size,
                file_type=req.file_type,
                is_from_client=req.is_from_client
            )
            self.session.add(order_file)
            self.session.flush()
            return order_file
        except SQLAlchemyError as exc:
            logger.error("[CreateOrderFile] DB error: %s", exc)
            raise DatabaseError(str(exc)) from exc

class GetOrderFileById:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, file_id: str, order_id: str) -> OrderFile:
        try:
            stmnt = select(OrderFile).where(
                OrderFile.order_id == order_id,
                OrderFile.id == file_id
            )
            order_file = self.session.execute(stmnt).scalar_one_or_none()
            if not order_file:
                raise NotFound("File not found")
            return order_file
        except SQLAlchemyError as exc:
            logger.error("[GetOrderFileById] DB error: %s", exc)
            raise DatabaseError(str(exc)) from exc