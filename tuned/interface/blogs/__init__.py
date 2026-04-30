from __future__ import annotations
from typing import Optional, TYPE_CHECKING
from tuned.interface.blogs.categories import BlogCategoryService
from tuned.interface.blogs.posts import BlogPostService
from tuned.interface.blogs.comments import BlogCommentService
from tuned.interface.blogs.reactions import CommentReactionService

if TYPE_CHECKING:
    from tuned.repository import Repository

class Blogs:
    def __init__(self, repos: Repository) -> None:
        self._repos = repos
        self._post: BlogPostService | None = None
        self._category: BlogCategoryService | None = None
        self._comment: BlogCommentService | None = None
        self._reaction: CommentReactionService | None = None

    @property
    def post(self) -> BlogPostService:
        if not self._post:
            self._post = BlogPostService(repos=self._repos)
        return self._post

    @property
    def category(self) -> BlogCategoryService:
        if not self._category:
            self._category = BlogCategoryService(repos=self._repos)
        return self._category

    @property
    def comment(self) -> BlogCommentService:
        if not self._comment:
            self._comment = BlogCommentService(repos=self._repos)
        return self._comment

    @property
    def reaction(self) -> CommentReactionService:
        if not self._reaction:
            self._reaction = CommentReactionService(repos=self._repos)
        return self._reaction

__all__ = [
    "Blogs",
    "BlogPostService",
    "BlogCategoryService",
    "BlogCommentService",
    "CommentReactionService"
]