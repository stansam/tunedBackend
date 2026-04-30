from __future__ import annotations
import logging
from typing import List, Optional, TYPE_CHECKING

from tuned.dtos import BlogCommentDTO, BlogCommentResponseDTO
from tuned.repository.exceptions import AlreadyExists, DatabaseError, NotFound
from tuned.core.logging import get_logger

if TYPE_CHECKING:
    from tuned.repository import Repository

logger: logging.Logger = get_logger(__name__)


class BlogCommentService:
    def __init__(self, repos: Repository) -> None:
        self._repo = repos.blog

    def create_comment(self, data: BlogCommentDTO) -> BlogCommentResponseDTO:
        try:
            logger.debug("Creating blog comment: %s", data.name)
            return self._repo.create_blog_comment(data)
        except AlreadyExists:
            logger.error("Blog comment already exists: %s", data.name)
            raise AlreadyExists("comment already exists")
        except DatabaseError:
            logger.error("Database error while creating comment")
            raise DatabaseError("Database error while creating comment")

    def get_comment(self, id: str) -> BlogCommentResponseDTO:
        try:
            logger.debug("Fetching blog comment: %s", id)
            return self._repo.get_blog_comment(id)
        except NotFound:
            logger.error("Blog comment not found: %s", id)
            raise NotFound("comment not found")
        except DatabaseError:
            logger.error("Database error while fetching comment")
            raise DatabaseError("Database error while fetching comment")

    def update_or_delete_comment(self, id: str, data: BlogCommentDTO) -> BlogCommentResponseDTO:
        try:
            logger.debug("Updating or deleting blog comment: %s", id)
            return self._repo.update_or_delete_comment(id, data)
        except NotFound:
            logger.error("Blog comment not found: %s", id)
            raise NotFound("comment not found")
        except DatabaseError:
            logger.error("Database error while updating comment")
            raise DatabaseError("Database error while updating comment")

    def get_blog_comments(self, post_id: str) -> List[BlogCommentResponseDTO]:
        try:
            logger.debug("Fetching blog comments for post: %s", post_id)
            return self._repo.get_blog_comments(post_id)
        except DatabaseError:
            logger.error("Database error while fetching comments")
            raise DatabaseError("Database error while fetching comments")