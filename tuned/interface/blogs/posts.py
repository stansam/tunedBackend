import logging
from typing import List

from tuned.dtos import BlogPostDTO, BlogPostResponseDTO
from tuned.models import BlogPost
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
        logger.info("Creating blog post: %s", data.title)
        post = self._repo.create_blog(data)
        logger.info("Blog post created: id=%s", post.id)
        return post

    def get_by_slug(self, slug: str) -> BlogPostResponseDTO:
        """Retrieve a blog post by its URL slug.

        Raises:
            NotFound: If no post exists with the given slug.
            DatabaseError: On unexpected database failure.
        """
        return self._repo.get_blog_post_by_slug(slug)

    def list_featured(self) -> List[BlogPostResponseDTO]:
        """Return featured blog posts."""
        return self._repo.get_featured()

    def list_published(self) -> List[BlogPostResponseDTO]:
        """Return all published blog posts ordered by most recent."""
        return self._repo.get_published()