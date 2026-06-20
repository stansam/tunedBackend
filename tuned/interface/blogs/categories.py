from __future__ import annotations
import logging, copy
from typing import List, Optional, TYPE_CHECKING

from tuned.dtos import BlogCategoryDTO, BlogCategoryResponseDTO, ActivityLogCreateDTO
from tuned.repository.exceptions import AlreadyExists, DatabaseError, NotFound
from tuned.core.logging import get_logger
from tuned.utils.variables import Variables

if TYPE_CHECKING:
    from tuned.repository import Repository
    from tuned.interface import Services

logger: logging.Logger = get_logger(__name__)

class BlogCategoryService:
    def __init__(self, repos: Repository, services: Services) -> None:
        self._repo = repos.blog
        self._audit_service = services.audit.activity_log

    def create_category(self, data: BlogCategoryDTO, actor_id: Optional[str] = None, ip_address: Optional[str] = "system", user_agent: Optional[str] = "system") -> BlogCategoryResponseDTO:
        try:
            logger.debug("Creating blog category: %s", data.name)
            category = self._repo.create_blog_category(data)
            logger.debug("Blog category created: id=%s slug=%s", category.id, category.slug)
            # return category
        except AlreadyExists:
            logger.error("Blog category already exists: %s", data.name)
            raise AlreadyExists("category already exists")
        except DatabaseError:
            logger.error("Database error while creating category")
            raise DatabaseError("Database error while creating category")
        
        try:
            self._audit_service.log(ActivityLogCreateDTO(
                action=Variables.BLOG_CATEGORY_CREATED,
                user_id=actor_id,
                entity_type=Variables.BLOG_CATEGORY_ENTITY_TYPE,
                entity_id=str(category.id),
                after=category,
                created_by=actor_id,
                ip_address=ip_address,
                user_agent=user_agent
            ))
        except Exception as audit_exc:
            logger.error("[BlogCommentService.create_comment] Audit failed: %r", audit_exc)

        return BlogCategoryResponseDTO.from_model(category)

    def get_by_slug(self, slug: str) -> BlogCategoryResponseDTO:
        try:
            logger.debug("Fetching blog category: %s", slug)
            category = self._repo.get_blog_category_by_slug(slug)
            return BlogCategoryResponseDTO.from_model(category)
        except NotFound:
            logger.error("Blog category not found: %s", slug)
            raise NotFound("category not found")
        except DatabaseError:
            logger.error("Database error while fetching category")
            raise DatabaseError("Database error while fetching category")

    def list_categories(self) -> List[BlogCategoryResponseDTO]:
        try:
            logger.debug("Fetching all blog categories")
            categories = self._repo.list_blog_categories()
            return [BlogCategoryResponseDTO.from_model(category) for category in categories]
        except DatabaseError:
            logger.error("Database error while fetching categories")
            raise DatabaseError("Database error while fetching categories")

    def update_or_delete_category(self, id: str, data: BlogCategoryDTO, actor_id: Optional[str] = None, ip_address: Optional[str] = "system", user_agent: Optional[str] = "system") -> BlogCategoryResponseDTO:
        is_delete = data.is_deleted
        err_str = "Deleting" if is_delete else "Updating"
        try:
            logger.debug(f"{err_str} blog category: {id}")
            existing = copy.deepcopy(self._repo.get_blog_category_by_id(id))
            category = self._repo.update_or_delete_category(id, data)
        except NotFound:
            logger.error(f"Blog category not found: {id}")
            raise NotFound("category not found")
        except DatabaseError as err:
            logger.error(f"Database error while {err_str.lower()} category: {err}")
            raise DatabaseError(f"Database error while {err_str.lower()} category: {err}")
        
        try:
            action_type = Variables.BLOG_CATEGORY_UPDATED if is_delete else Variables.BLOG_CATEGORY_DELETED
            self._audit_service.log(ActivityLogCreateDTO(
                action=action_type,
                user_id=actor_id,
                entity_type=Variables.BLOG_CATEGORY_ENTITY_TYPE,
                entity_id=id,
                before=existing,
                after=category,
                created_by=actor_id,
                ip_address=ip_address,
                user_agent=user_agent
            ))
        except Exception as audit_exc:
            logger.error("[BlogCommentService.update_or_delete_comment] Audit failed: %r", audit_exc)
        
        return BlogCategoryResponseDTO.from_model(category)
