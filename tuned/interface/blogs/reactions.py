from __future__ import annotations
import logging
from typing import List, Optional, TYPE_CHECKING

from tuned.dtos import CommentReactionDTO, CommentReactionResponseDTO, ActivityLogCreateDTO
from tuned.repository.exceptions import AlreadyExists, DatabaseError, NotFound
from tuned.core.logging import get_logger
from tuned.utils.variables import Variables

if TYPE_CHECKING:
    from tuned.repository import Repository
    from tuned.interface import Services

logger: logging.Logger = get_logger(__name__)


class CommentReactionService:
    def __init__(self, repos: Repository, services: Services) -> None:
        self._repo = repos.blog
        self._services = services
        self._audit_service = services.audit.activity_log

    def create_comment_reaction(self, data: CommentReactionDTO, user_agent: Optional[str] = "system", ip_address: Optional[str] = "system") -> CommentReactionResponseDTO:
        try:
            logger.debug("Creating comment reaction of type '%s'", data.reaction_type)
            comment = self._repo.create_comment_reaction(data)
        except AlreadyExists:
            logger.error("Comment reaction already exists for type '%s'", data.reaction_type)
            raise AlreadyExists("reaction already exists")
        except DatabaseError:
            logger.error("Database error while creating reaction")
            raise DatabaseError("Database error while creating reaction")
        try:
            self._audit_service.log(ActivityLogCreateDTO(
                user_id=data.user_id,
                action=Variables.BLOG_COMMENT_REACTION_CREATED,
                entity_type=Variables.BLOG_COMMENT_REACTION_ENTITY_TYPE,
                entity_id=str(comment.id),
                after=comment,
                user_agent=user_agent,
                ip_address=ip_address
            ))
        except Exception as e:
            logger.error("Error while logging reaction activity: %s", str(e))
        
        return CommentReactionResponseDTO.from_model(comment)


    def get_comment_reaction(self, id: str) -> CommentReactionResponseDTO:
        try:
            logger.debug("Fetching comment reaction: %s", id)
            reaction = self._repo.get_comment_reaction(id)
            return CommentReactionResponseDTO.from_model(reaction)
        except NotFound:
            logger.error("Comment reaction not found: %s", id)
            raise NotFound("reaction not found")
        except DatabaseError:
            logger.error("Database error while fetching reaction")
            raise DatabaseError("Database error while fetching reaction")

    def update_or_delete_comment_reaction(self, id: str, data: CommentReactionDTO, ip_address: Optional[str] = "system", user_agent: Optional[str] = "system") -> CommentReactionResponseDTO:
        is_delete = data.is_deleted
        err_str = "Updating" if not is_delete else "Deleting"
        try:
            logger.debug("%s comment reaction: %s", err_str, id)
            reaction = self._repo.update_or_delete_comment_reaction(id, data)
        except NotFound:
            logger.error("Comment reaction not found: %s", id)
            raise NotFound("reaction not found")
        except DatabaseError as err:
            logger.error("Database error while %s reaction: %s", err_str.lower(), err)
            raise DatabaseError("Database error while %s reaction" % err_str.lower())

        try:
            if data.is_deleted:
                self._audit_service.log(ActivityLogCreateDTO(
                    user_id=data.user_id,
                    action=Variables.BLOG_COMMENT_REACTION_DELETED,
                    entity_type=Variables.BLOG_COMMENT_REACTION_ENTITY_TYPE,
                    entity_id=str(reaction.id),
                    after=reaction,
                    user_agent=user_agent,
                    ip_address=ip_address
                ))
            else:
                self._audit_service.log(ActivityLogCreateDTO(
                    user_id=data.user_id,
                    action=Variables.BLOG_COMMENT_REACTION_UPDATED,
                    entity_type=Variables.BLOG_COMMENT_REACTION_ENTITY_TYPE,
                    entity_id=str(reaction.id),
                    before=reaction,
                    after=reaction,
                    user_agent=user_agent,
                    ip_address=ip_address
                ))
        except Exception as e:
            logger.error("Error while logging reaction activity: %s", str(e))
        
        return CommentReactionResponseDTO.from_model(reaction)

    def get_comment_reactions(self, comment_id: str) -> List[CommentReactionResponseDTO]:
        try:
            logger.debug("Fetching reactions for comment: %s", comment_id)
            reactions = self._repo.get_comment_reactions(comment_id)
            return [CommentReactionResponseDTO.from_model(reaction) for reaction in reactions]
        except DatabaseError:
            logger.error("Database error while fetching reactions")
            raise DatabaseError("Database error while fetching reactions")