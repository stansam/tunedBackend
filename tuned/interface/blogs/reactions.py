import logging
from typing import List

from tuned.dtos import CommentReactionDTO, CommentReactionResponseDTO
from tuned.repository import repositories
from tuned.repository.exceptions import AlreadyExists, DatabaseError, NotFound

logger = logging.getLogger(__name__)


class CommentReactionService:
    """Service layer for BlogCategory business logic."""

    def __init__(self) -> None:
        self._repo = repositories.blog

    def create_comment(self, data: CommentReactionDTO) -> CommentReactionResponseDTO:
        try:
            return self._repo.create_comment_reaction(data)
        except AlreadyExists:
            raise AlreadyExists("comment already exists")
        except DatabaseError:
            raise DatabaseError("Database error while creating comment")

    def get_comment(self, id: str) -> CommentReactionResponseDTO:
        try:
            return self._repo.get_comment_reaction(id)
        except NotFound:
            raise NotFound("comment not found")
        except DatabaseError:
            raise DatabaseError("Database error while fetching comment")

    def update_or_delete_comment(self, id: str, data: CommentReactionDTO) -> CommentReactionResponseDTO:
        try:
            return self._repo.update_or_delete_comment_reaction(id, data)
        except NotFound:
            raise NotFound("comment not found")
        except DatabaseError:
            raise DatabaseError("Database error while updating comment")

    def get_blog_comments(self, post_id: str) -> List[CommentReactionResponseDTO]:
        try:
            return self._repo.get_comment_reactions(post_id)
        except DatabaseError:
            raise DatabaseError("Database error while fetching comments")