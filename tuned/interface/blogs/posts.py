from __future__ import annotations
import logging, copy
from typing import List, TYPE_CHECKING, Optional

from tuned.dtos import (
    BlogPostDTO, 
    BlogPostResponseDTO, 
    BlogPostListResponseDTO, 
    BlogPostListRequestDTO, 
    PostByCategoryRequestDTO,
    ActivityLogCreateDTO
)
from tuned.repository.exceptions import AlreadyExists, DatabaseError, NotFound
from tuned.core.logging import get_logger
from tuned.utils.variables import Variables
if TYPE_CHECKING:
    from tuned.repository import Repository
    from tuned.interface import Services

logger: logging.Logger = get_logger(__name__)


class BlogPostService:
    def __init__(self, repos: Repository, services: Services) -> None:
        self._repo = repos.blog
        self._audit_service = services.audit.activity_log
        # self._services = services

    def create_post(self, data: BlogPostDTO, actor_id: Optional[str] = None, ip_address: str = "system", user_agent: str = "system") -> BlogPostResponseDTO:
        try:
            logger.info("Creating blog post: %s", data.title)
            post = self._repo.create_blog(data)
            logger.info("Blog post created: id=%s", post.id)
            # return post
        except AlreadyExists:
            logger.error("Post already exists: %s", data.title)
            raise AlreadyExists("post already exists")
        except DatabaseError:
            logger.error("Database error while creating post")
            raise DatabaseError("Database error while creating post")

        try:
            self._audit_service.log(ActivityLogCreateDTO(
                action=Variables.BLOG_POST_CREATED,
                user_id=actor_id,
                entity_type=Variables.BLOG_POST_ENTITY_TYPE,
                entity_id=str(post.id),
                after=post,
                created_by=actor_id,
                ip_address=ip_address,
                user_agent=user_agent
            ))
        except Exception as audit_exc:
            logger.error("[BlogPostService.create_post] Audit failed: %r", audit_exc)

        return BlogPostResponseDTO.from_model(post)    

    def get_by_slug(self, slug: str) -> BlogPostResponseDTO:
        try:
            logger.debug("Fetching blog post: %s", slug)
            post = self._repo.get_blog_post_by_slug(slug)
            return BlogPostResponseDTO.from_model(post)
        except NotFound:
            logger.error("Post not found: %s", slug)
            raise NotFound("post not found")
        except DatabaseError:
            logger.error("Database error while fetching post")
            raise DatabaseError("Database error while fetching post")
    
    def get_by_id(self, id: str) -> BlogPostResponseDTO:
        try:
            logger.debug("Fetching blog post: %s", id)
            post = self._repo.get_blog_post_by_id(id)
            return BlogPostResponseDTO.from_model(post)
        except NotFound:
            logger.error("Post not found: %s", id)
            raise NotFound("post not found")
        except DatabaseError:
            logger.error("Database error while fetching post")
            raise DatabaseError("Database error while fetching post")


    def list_featured(self) -> List[BlogPostResponseDTO]:
        try:
            logger.debug("Fetching featured blog posts")
            posts = self._repo.get_featured()
            return [BlogPostResponseDTO.from_model(post) for post in posts]
        except DatabaseError:
            logger.error("Database error while fetching featured posts")
            raise DatabaseError("Database error while fetching featured posts")

    def list_published(self, req: BlogPostListRequestDTO) -> BlogPostListResponseDTO:
        try:
            logger.debug("Fetching published blog posts")
            return self._repo.get_published(req)
        except DatabaseError:
            logger.error("Database error while fetching published posts")
            raise DatabaseError("Database error while fetching published posts")
    
    def update_or_delete_post(self, id: str, data: BlogPostDTO, actor_id: Optional[str] = None, ip_address: str = "system", user_agent: str = "system") -> BlogPostResponseDTO:
        is_delete = data.is_deleted
        try:
            post_to_update = self._repo.get_blog_post_by_id(id)
            existing = copy.deepcopy(post_to_update)
            logger.debug("Updating blog post: %s" if not is_delete else "Deleting blog post: %s", id)

            post = self._repo.update_or_delete_post(id, data)
        except NotFound:
            logger.error("Post not found: %s", id)
            raise NotFound("post not found")
        except DatabaseError as err:
            err_str = "Database error while updating post" if not is_delete else "Database error while deleting post"
            logger.error(f"{err_str}: {err}")
            raise DatabaseError(err_str)
        try:
            self._audit_service.log(ActivityLogCreateDTO(
                action=Variables.BLOG_POST_UPDATED if not is_delete else Variables.BLOG_POST_DELETED,
                user_id=actor_id,
                entity_type=Variables.BLOG_POST_ENTITY_TYPE,
                entity_id=str(post.id),
                before=existing,
                after=post,
                created_by=actor_id,
                ip_address=ip_address,
                user_agent=user_agent
            ))
        except Exception as audit_exc:
            logger.error("[BlogPostService.update_or_delete_post] Audit failed: %r", audit_exc)
        return BlogPostResponseDTO.from_model(post)
    def get_by_category(self, req: PostByCategoryRequestDTO) -> List[BlogPostResponseDTO]:
        try:
            logger.debug("Fetching blog posts for category: %s", req.category_id)
            posts = self._repo.get_by_category(req)
            return [BlogPostResponseDTO.from_model(post) for post in posts]
        except DatabaseError:
            logger.error("Database error while fetching posts by category")
            raise DatabaseError("Database error while fetching posts")
    
    def get_related(self, slug: str) -> List[BlogPostResponseDTO]:
        try:
            logger.debug("Fetching related blog posts for: %s", slug)
            post = self.get_by_slug(slug)
            if not post.category_id:
                return []
            return self.get_by_category(PostByCategoryRequestDTO(category_id=post.category_id, exclude=slug, per_page=3))
        except NotFound:
            return []
        except DatabaseError:
            logger.error("Database error while fetching related posts")
            raise DatabaseError("Database error while fetching posts")