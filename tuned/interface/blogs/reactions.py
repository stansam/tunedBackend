from __future__ import annotations
import logging
from typing import List, Optional, TYPE_CHECKING

from tuned.dtos import CommentReactionDTO, CommentReactionResponseDTO
from tuned.repository.exceptions import AlreadyExists, DatabaseError, NotFound
from tuned.core.logging import get_logger

if TYPE_CHECKING:
    from tuned.repository import Repository

logger: logging.Logger = get_logger(__name__)


class CommentReactionService:
    def __init__(self, repos: Optional[Repository] = None) -> None:
        if repos:
            self._repo = repos.blog
        else:
            from tuned.repository import repositories
            self._repo = repositories.blog

    def create_comment_reaction(self, data: CommentReactionDTO) -> CommentReactionResponseDTO:
        try:
            logger.debug("Creating comment reaction of type '%s'", data.reaction_type)
            return self._repo.create_comment_reaction(data)
        except AlreadyExists:
            logger.error("Comment reaction already exists for type '%s'", data.reaction_type)
            raise AlreadyExists("reaction already exists")
        except DatabaseError:
            logger.error("Database error while creating reaction")
            raise DatabaseError("Database error while creating reaction")


    def get_comment_reaction(self, id: str) -> CommentReactionResponseDTO:
        try:
            logger.debug("Fetching comment reaction: %s", id)
            return self._repo.get_comment_reaction(id)
        except NotFound:
            logger.error("Comment reaction not found: %s", id)
            raise NotFound("reaction not found")
        except DatabaseError:
            logger.error("Database error while fetching reaction")
            raise DatabaseError("Database error while fetching reaction")

    def update_or_delete_comment_reaction(self, id: str, data: CommentReactionDTO) -> CommentReactionResponseDTO:
        try:
            logger.debug("Updating or deleting comment reaction: %s", id)
            return self._repo.update_or_delete_comment_reaction(id, data)
        except NotFound:
            logger.error("Comment reaction not found: %s", id)
            raise NotFound("reaction not found")
        except DatabaseError:
            logger.error("Database error while updating reaction")
            raise DatabaseError("Database error while updating reaction")

    def get_comment_reactions(self, comment_id: str) -> List[CommentReactionResponseDTO]:
        try:
            logger.debug("Fetching reactions for comment: %s", comment_id)
            return self._repo.get_comment_reactions(comment_id)
        except DatabaseError:
            logger.error("Database error while fetching reactions")
            raise DatabaseError("Database error while fetching reactions")