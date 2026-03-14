import logging
from typing import List

from tuned.dtos import BlogCategoryDTO
from tuned.models import BlogCategory
from tuned.repository import repositories
from tuned.repository.exceptions import AlreadyExists, DatabaseError, NotFound

logger = logging.getLogger(__name__)


class BlogCategoryService:
    """Service layer for BlogCategory business logic."""

    def __init__(self) -> None:
        self._repo = repositories.blog

    def create_category(self, data: BlogCategoryDTO) -> BlogCategory:
        """Create a new blog category.

        Raises:
            AlreadyExists: If a category with this slug already exists.
            DatabaseError: On unexpected database failure.
        """
        logger.info("Creating blog category: %s", data.name)
        category = self._repo.create_blog_category(data)
        logger.info("Blog category created: id=%s slug=%s", category.id, category.slug)
        return category

    def get_by_slug(self, slug: str) -> BlogCategory:
        """Retrieve a blog category by its URL slug.

        Raises:
            NotFound: If no category exists with the given slug.
            DatabaseError: On unexpected database failure.
        """
        return self._repo.get_blog_category_by_slug(slug)

    def list_categories(self) -> List[BlogCategory]:
        """Return all blog categories."""
        return self._repo.list_blog_categories()
