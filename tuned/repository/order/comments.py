from __future__ import annotations
import logging
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload
from tuned.models.order import OrderComment, OrderFile
from tuned.core.exceptions import DatabaseError, NotFound
from tuned.core.logging import get_logger

logger: logging.Logger = get_logger(__name__)

class GetOrderComments:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, order_id: str) -> list[OrderComment]:
        try:
            stmt = (
                select(OrderComment)
                .options(
                    joinedload(OrderComment.user),
                    joinedload(OrderComment.attachments),
                )
                .where(
                    OrderComment.order_id == order_id,
                    OrderComment.is_deleted == False,
                )
                .order_by(OrderComment.created_at.asc())
            )
            return list(self.session.scalars(stmt).unique().all())
        except SQLAlchemyError as exc:
            logger.error("[GetOrderComments] DB error: %s", exc)
            raise DatabaseError(str(exc)) from exc


class CreateOrderComment:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, order_id: str, user_id: str, content: str, is_admin: bool = False) -> OrderComment:
        try:
            comment = OrderComment(
                order_id=order_id,
                user_id=user_id,
                message=content,
                is_admin=is_admin,
                is_read=False,
            )
            self.session.add(comment)
            self.session.flush()
            return comment
        except SQLAlchemyError as exc:
            logger.error("[CreateOrderComment] DB error: %s", exc)
            raise DatabaseError(str(exc)) from exc


class UpdateOrderComment:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, comment_id: str, user_id: str, content: str) -> OrderComment:
        try:
            stmt = (
                select(OrderComment)
                .where(
                    OrderComment.id == comment_id,
                    OrderComment.user_id == user_id,
                    OrderComment.is_deleted == False,
                )
            )
            comment = self.session.scalar(stmt)
            if not comment:
                raise NotFound(f"Comment {comment_id} not found")
            comment.message = content
            comment.updated_at = datetime.now(timezone.utc)
            self.session.flush()
            return comment
        except NotFound:
            raise
        except SQLAlchemyError as exc:
            logger.error("[UpdateOrderComment] DB error: %s", exc)
            raise DatabaseError(str(exc)) from exc


class DeleteOrderComment:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, comment_id: str, user_id: str) -> None:
        try:
            stmt = (
                select(OrderComment)
                .where(
                    OrderComment.id == comment_id,
                    OrderComment.user_id == user_id,
                    OrderComment.is_deleted == False,
                )
            )
            comment = self.session.scalar(stmt)
            if not comment:
                raise NotFound(f"Comment {comment_id} not found")
            comment.is_deleted = True
            comment.deleted_at = datetime.now(timezone.utc)
            comment.deleted_by = UUID(user_id)
            self.session.flush()
        except NotFound:
            raise
        except SQLAlchemyError as exc:
            logger.error("[DeleteOrderComment] DB error: %s", exc)
            raise DatabaseError(str(exc)) from exc


class LinkFilesToComment:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, comment_id: str, file_ids: list[str]) -> None:
        if not file_ids:
            return
        try:
            stmt = (
                update(OrderFile)
                .where(OrderFile.id.in_(file_ids))
                .values(comment_id=comment_id)
            )
            self.session.execute(stmt)
            self.session.flush()
        except SQLAlchemyError as exc:
            logger.error("[LinkFilesToComment] DB error: %s", exc)
            raise DatabaseError(str(exc)) from exc


class MarkCommentsRead:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, order_id: str, reader_user_id: str) -> None:
        try:
            stmt = (
                update(OrderComment)
                .where(
                    OrderComment.order_id == order_id,
                    OrderComment.user_id != reader_user_id,
                    OrderComment.is_read == False,
                    OrderComment.is_deleted == False,
                )
                .values(is_read=True)
            )
            self.session.execute(stmt)
            self.session.flush()
        except SQLAlchemyError as exc:
            logger.error("[MarkCommentsRead] DB error: %s", exc)
            raise DatabaseError(str(exc)) from exc
