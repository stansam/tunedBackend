from __future__ import annotations
import logging, copy
from typing import List, Optional, TYPE_CHECKING

from tuned.dtos import BlogCommentDTO, BlogCommentResponseDTO, ActivityLogCreateDTO
from tuned.repository.exceptions import AlreadyExists, DatabaseError, NotFound
from tuned.core.logging import get_logger
from tuned.utils.variables import Variables

if TYPE_CHECKING:
    from tuned.repository import Repository
    from tuned.interface import Services

logger: logging.Logger = get_logger(__name__)


class BlogCommentService:
    def __init__(self, repos: Repository, services: Services) -> None:
        self._repo = repos.blog
        self._audit_service = services.audit.activity_log

    def create_comment(self, data: BlogCommentDTO, actor_id: Optional[str] = None, ip_address: Optional[str] = "system", user_agent: Optional[str] = "system") -> BlogCommentResponseDTO:
        try:
            logger.debug("Creating blog comment: %s", data.name)
            comment = self._repo.create_blog_comment(data)
        except AlreadyExists:
            logger.error("Blog comment already exists: %s", data.name)
            raise AlreadyExists("comment already exists")
        except DatabaseError:
            logger.error("Database error while creating comment")
            raise DatabaseError("Database error while creating comment")
        
        try:
            self._audit_service.log(ActivityLogCreateDTO(
                action=Variables.BLOG_COMMENT_CREATED,
                user_id=actor_id,
                entity_type=Variables.BLOG_COMMENT_ENTITY_TYPE,
                entity_id=str(comment.id),
                after=comment,
                created_by=actor_id,
                ip_address=ip_address,
                user_agent=user_agent
            ))
        except Exception as audit_exc:
            logger.error("[BlogCommentService.create_comment] Audit failed: %r", audit_exc)

        return BlogCommentResponseDTO.from_model(comment)


    def get_comment(self, id: str) -> BlogCommentResponseDTO:
        try:
            logger.debug("Fetching blog comment: %s", id)
            comment = self._repo.get_blog_comment(id)
            return BlogCommentResponseDTO.from_model(comment)
        except NotFound:
            logger.error("Blog comment not found: %s", id)
            raise NotFound("comment not found")
        except DatabaseError:
            logger.error("Database error while fetching comment")
            raise DatabaseError("Database error while fetching comment")

    def update_or_delete_comment(self, id: str, data: BlogCommentDTO, actor_id: Optional[str] = None, ip_address: Optional[str] = "system", user_agent: Optional[str] = "system") -> BlogCommentResponseDTO:
        is_delete = data.is_deleted
        try:
            logger.debug("Updating blog comment: %s" if not is_delete else "Deleting blog comment: %s", id)
            existing = copy.deepcopy(self._repo.get_blog_comment(id))
            comment = self._repo.update_or_delete_comment(id, data)
        except NotFound:
            logger.error("Blog comment not found: %s", id)
            raise NotFound("comment not found")
        except DatabaseError as err:
            logger.error("Database error while updating comment: %s" if not is_delete else "Database error while deleting comment: %s", err)
            raise DatabaseError("Database error while updating comment: " + str(err) if not is_delete else "Database error while deleting comment: " + str(err))

        try:
            self._audit_service.log(ActivityLogCreateDTO(
                action=Variables.BLOG_COMMENT_UPDATED if not is_delete else Variables.BLOG_COMMENT_DELETED,
                user_id=actor_id,
                entity_type=Variables.BLOG_COMMENT_ENTITY_TYPE,
                entity_id=str(comment.id),
                before=existing,
                after=comment,
                created_by=actor_id,
                ip_address=ip_address,
                user_agent=user_agent
            ))
        except Exception as audit_exc:
            logger.error("[BlogCommentService.update_or_delete_comment] Audit failed: %r", audit_exc)

        return BlogCommentResponseDTO.from_model(comment)

    def get_blog_comments(self, post_id: str) -> List[BlogCommentResponseDTO]:
        try:
            logger.debug("Fetching blog comments for post: %s", post_id)
            comments = self._repo.get_blog_comments(post_id)
            return [BlogCommentResponseDTO.from_model(comment) for comment in comments]
        except DatabaseError:
            logger.error("Database error while fetching comments")
            raise DatabaseError("Database error while fetching comments")