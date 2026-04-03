from tuned.interface.blogs.categories import BlogCategoryService
from tuned.interface.blogs.posts import BlogPostService
from tuned.interface.blogs.comments import BlogCommentService
from tuned.interface.blogs.reactions import CommentReactionService

# class BlogsService:
#     """Service facade for blog listing operations."""

#     def __init__(self):
#         self._repo = repositories.blog

#     def list_featured_blogs(self) -> BlogPostResponseDTO:
#         return self._repo.get_featured()


__all__ = [
    "BlogPostService",
    "BlogCategoryService",
    "BlogCommentService",
    "CommentReactionService"
]