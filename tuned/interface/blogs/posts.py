import logging
from typing import List

from tuned.dtos import BlogPostDTO, BlogPostResponseDTO, BlogPostListResponseDTO, BlogPostListRequestDTO
from tuned.repository import repositories
from tuned.repository.exceptions import AlreadyExists, DatabaseError, NotFound

logger = logging.getLogger(__name__)


class BlogPostService:
    """Service layer for BlogPost business logic."""

    def __init__(self) -> None:
        self._repo = repositories.blog

    def create_post(self, data: BlogPostDTO) -> BlogPostResponseDTO:
        """Create a new blog post.

        Raises:
            AlreadyExists: If a post with this title or slug already exists.
            DatabaseError: On unexpected database failure.
        """
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
        """Retrieve a blog post by its URL slug.

        Raises:
            NotFound: If no post exists with the given slug.
            DatabaseError: On unexpected database failure.
        """
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
        """Retrieve a blog post by its URL id.

        Raises:
            NotFound: If no post exists with the given id.
            DatabaseError: On unexpected database failure.
        """
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
        """Return featured blog posts."""
        try:
            logger.debug("Fetching featured blog posts")
            return self._repo.get_featured()
        except DatabaseError:
            logger.error("Database error while fetching featured posts")
            raise DatabaseError("Database error while fetching featured posts")

    def list_published(self, req: BlogPostListRequestDTO) -> BlogPostListResponseDTO:
        """Return all published blog posts ordered by most recent."""
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
