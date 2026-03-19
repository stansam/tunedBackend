from tuned.repository import repositories
from tuned.interface.blogs.categories import BlogCategoryService
from tuned.interface.blogs.posts import BlogPostService
from tuned.dtos import BlogPostResponseDTO

class BlogsService:
    """Service facade for blog listing operations."""

    def __init__(self):
        self._repo = repositories.blog

    def list_featured_blogs(self) -> BlogPostResponseDTO:
        return self._repo.get_featured()


__all__ = ["BlogsService", "BlogCategoryService", "BlogPostService"]