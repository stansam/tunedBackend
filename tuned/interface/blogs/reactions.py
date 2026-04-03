import logging
from typing import List

from tuned.dtos import CommentReactionDTO, CommentReactionResponseDTO
from tuned.repository import repositories
from tuned.repository.exceptions import AlreadyExists, DatabaseError, NotFound
from tuned.core.logging import get_logger

logger: logging.Logger = get_logger(__name__)


class CommentReactionService:
    def __init__(self) -> None:
        self._repo = repositories.blog

    def create_comment(self, data: CommentReactionDTO) -> CommentReactionResponseDTO:
        try:
            logger.debug("Creating comment reaction: %s", data.name)
            return self._repo.create_comment_reaction(data)
        except AlreadyExists:
            logger.error("Comment reaction already exists: %s", data.name)
            raise AlreadyExists("comment already exists")
        except DatabaseError:
            logger.error("Database error while creating comment")
            raise DatabaseError("Database error while creating comment")

    def get_comment(self, id: str) -> CommentReactionResponseDTO:
        try:
            logger.debug("Fetching comment reaction: %s", id)
            return self._repo.get_comment_reaction(id)
        except NotFound:
            logger.error("Comment reaction not found: %s", id)
            raise NotFound("comment not found")
        except DatabaseError:
            logger.error("Database error while fetching comment")
            raise DatabaseError("Database error while fetching comment")

    def update_or_delete_comment(self, id: str, data: CommentReactionDTO) -> CommentReactionResponseDTO:
        try:
            logger.debug("Updating or deleting comment reaction: %s", id)
            return self._repo.update_or_delete_comment_reaction(id, data)
        except NotFound:
            logger.error("Comment reaction not found: %s", id)
            raise NotFound("comment not found")
        except DatabaseError:
            logger.error("Database error while updating comment")
            raise DatabaseError("Database error while updating comment")

    def get_blog_comments(self, post_id: str) -> List[CommentReactionResponseDTO]:
        try:
            logger.debug("Fetching blog comments for post: %s", post_id)
            return self._repo.get_comment_reactions(post_id)
        except DatabaseError:
            logger.error("Database error while fetching comments")
            raise DatabaseError("Database error while fetching comments")