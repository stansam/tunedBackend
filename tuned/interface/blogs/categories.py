from tuned.dtos.blogs import BlogCategoryResponseDTO
import logging
from typing import List

from tuned.dtos import BlogCategoryDTO
from tuned.repository import repositories
from tuned.repository.exceptions import AlreadyExists, DatabaseError, NotFound
from tuned.core.logging import get_logger

logger: logging.Logger = get_logger(__name__)

class BlogCategoryService:
    def __init__(self) -> None:
        self._repo = repositories.blog

    def create_category(self, data: BlogCategoryDTO) -> BlogCategoryResponseDTO:
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
        try:
            logger.debug("Fetching all blog categories")
            return self._repo.list_blog_categories()
        except DatabaseError:
            logger.error("Database error while fetching categories")
            raise DatabaseError("Database error while fetching categories")

    
    def update_or_delete_category(self, id: str, data: BlogCategoryDTO) -> BlogCategoryResponseDTO:
        try:
            logger.debug("Updating or deleting blog category: %s", id)
            return self._repo.update_or_delete_category(id, data)
        except NotFound:
            logger.error("Blog category not found: %s", id)
            raise NotFound("category not found")
        except DatabaseError:
            logger.error("Database error while updating or deleting category")
            raise DatabaseError("Database error while updating or deleting category")

