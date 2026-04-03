from tuned.dtos.blogs import BlogCategoryResponseDTO
import logging
from typing import List

from tuned.dtos import BlogCategoryDTO
from tuned.repository import repositories
from tuned.repository.exceptions import AlreadyExists, DatabaseError, NotFound

logger = logging.getLogger(__name__)


class BlogCategoryService:
    """Service layer for BlogCategory business logic."""

    def __init__(self) -> None:
        self._repo = repositories.blog

    def create_category(self, data: BlogCategoryDTO) -> BlogCategoryResponseDTO:
        """Create a new blog category.

        Raises:
            AlreadyExists: If a category with this slug already exists.
            DatabaseError: On unexpected database failure.
        """
        try:
            logger.debug("Creating blog category: %s", data.name)
            category = self._repo.create_blog_category(data)
            logger.debug("Blog category created: id=%s slug=%s", category.id, category.slug)
            return category
        except AlreadyExists:
            logger.error("Blog category already exists: %s", data.name)
            raise AlreadyExists("category already exists")
        except DatabaseError:
            logger.error("Database error while creating category")
            raise DatabaseError("Database error while creating category")

    def get_by_slug(self, slug: str) -> BlogCategoryResponseDTO:
        """Retrieve a blog category by its URL slug.

        Raises:
            NotFound: If no category exists with the given slug.
            DatabaseError: On unexpected database failure.
        """
        try:
            logger.debug("Fetching blog category: %s", slug)
            return self._repo.get_blog_category_by_slug(slug)
        except NotFound:
            logger.error("Blog category not found: %s", slug)
            raise NotFound("category not found")
        except DatabaseError:
            logger.error("Database error while fetching category")
            raise DatabaseError("Database error while fetching category")

    def list_categories(self) -> List[BlogCategoryResponseDTO]:
        """Return all blog categories."""
        try:
            logger.debug("Fetching all blog categories")
            return self._repo.list_blog_categories()
        except DatabaseError:
            logger.error("Database error while fetching categories")
            raise DatabaseError("Database error while fetching categories")

    
    def update_or_delete_category(self, id: str, data: BlogCategoryDTO) -> BlogCategoryResponseDTO:
        """Update or delete a blog category."""
        try:
            logger.debug("Updating or deleting blog category: %s", id)
            return self._repo.update_or_delete_category(id, data)
        except NotFound:
            logger.error("Blog category not found: %s", id)
            raise NotFound("category not found")
        except DatabaseError:
            logger.error("Database error while updating or deleting category")
            raise DatabaseError("Database error while updating or deleting category")

