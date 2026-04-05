import logging
from typing import List

from tuned.dtos import BlogPostDTO, BlogPostResponseDTO, BlogPostListResponseDTO, BlogPostListRequestDTO, PostByCategoryRequestDTO
from tuned.repository import repositories
from tuned.repository.exceptions import AlreadyExists, DatabaseError, NotFound
from tuned.core.logging import get_logger

logger: logging.Logger = get_logger(__name__)


class BlogPostService:
    def __init__(self) -> None:
        self._repo = repositories.blog

    def create_post(self, data: BlogPostDTO) -> BlogPostResponseDTO:
        try:
            logger.info("Creating blog post: %s", data.title)
            post = self._repo.create_blog(data)
            logger.info("Blog post created: id=%s", post.id)
            return post
        except AlreadyExists:
            logger.error("Post already exists: %s", data.title)
            raise AlreadyExists("post already exists")
        except DatabaseError:
            logger.error("Database error while creating post")
            raise DatabaseError("Database error while creating post")

    def get_by_slug(self, slug: str) -> BlogPostResponseDTO:
        try:
            logger.debug("Fetching blog post: %s", slug)
            return self._repo.get_blog_post_by_slug(slug)
        except NotFound:
            logger.error("Post not found: %s", slug)
            raise NotFound("post not found")
        except DatabaseError:
            logger.error("Database error while fetching post")
            raise DatabaseError("Database error while fetching post")
    
    def get_by_id(self, id: str) -> BlogPostResponseDTO:
        try:
            logger.debug("Fetching blog post: %s", id)
            return self._repo.get_blog_post_by_id(id)
        except NotFound:
            logger.error("Post not found: %s", id)
            raise NotFound("post not found")
        except DatabaseError:
            logger.error("Database error while fetching post")
            raise DatabaseError("Database error while fetching post")


    def list_featured(self) -> List[BlogPostResponseDTO]:
        try:
            logger.debug("Fetching featured blog posts")
            return self._repo.get_featured()
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
    
    def update_or_delete_post(self, id: str, data: BlogPostDTO) -> BlogPostResponseDTO:
        try:
            logger.debug("Updating or deleting blog post: %s", id)
            return self._repo.update_or_delete_post(id, data)
        except NotFound:
            logger.error("Post not found: %s", id)
            raise NotFound("comment not found")
        except DatabaseError:
            logger.error("Database error while updating or deleting post")
            raise DatabaseError("Database error while fetching comment")

    def get_by_category(self, req: PostByCategoryRequestDTO) -> BlogPostResponseDTO:
        try:
            logger.debug("Fetching blog post: %s", req.exclude)
            return self._repo.get_by_category(req)
        except NotFound:
            logger.error("Post not found: %s", req.exclude)
            raise NotFound("post not found")
        except DatabaseError:
            logger.error("Database error while fetching post")
            raise DatabaseError("Database error while fetching post")
    
    def get_related(self, slug: str) -> BlogPostResponseDTO:
        try:
            logger.debug("Fetching related blog posts: %s", slug)
            post = self.get_by_slug(slug)
            return self.get_by_category(PostByCategoryRequestDTO(category_id=post.category_id, exclude=slug, per_page=3))
        except NotFound:
            logger.error("Post not found: %s", slug)
            raise NotFound("post not found")
        except DatabaseError:
            logger.error("Database error while fetching post")
            raise DatabaseError("Database error while fetching post")