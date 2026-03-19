from typing import List
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from tuned.models import BlogPost, BlogCategory, BlogComment, CommentReaction
from tuned.repository.blogs.posts import (
    CreateBlog, GetBlogPostBySlug, GetFeaturedBlogPosts, GetPublishedBlogPosts
)
from tuned.repository.blogs.categories import (
    CreateBlogCategory, GetBlogCategoryBySlug, ListBlogCategories
)
from tuned.repository.blogs.comments import (
    CreateBlogComment, GetBlogComment
)
from tuned.repository.blogs.reactions import (
    CreateCommentReaction, GetCommentReaction
)
from tuned.dtos import (
    BlogCategoryDTO, BlogCommentDTO, BlogPostDTO, CommentReactionDTO
)
from tuned.extensions import db


class BlogRepository:
    def __init__(self):
        self.db = db
        self.session = db.session

    # Blog posts
    def create_blog(self, data: BlogPostDTO) -> BlogPostResponseDTO:
        return CreateBlog(self.session).execute(data)

    def get_blog_post_by_slug(self, slug: str) -> BlogPostResponseDTO:
        return GetBlogPostBySlug(self.session).execute(slug)

    def get_featured(self) -> List[BlogPostResponseDTO]:
        return GetFeaturedBlogPosts(self.session).execute()
    
    def get_published(self) -> List[BlogPostResponseDTO]:
        return GetPublishedBlogPosts(self.session).execute()

    # Blog categories
    def create_blog_category(self, data: BlogCategoryDTO) -> BlogCategory:
        return CreateBlogCategory(self.session).execute(data)

    def get_blog_category_by_slug(self, slug: str) -> BlogCategory:
        return GetBlogCategoryBySlug(self.session).execute(slug)
    
    def list_blog_categories(self) -> List[BlogCategory]:
        return ListBlogCategories(self.session).execute()

    # Blog comments
    def create_blog_comment(self, data: BlogCommentDTO) -> BlogComment:
        return CreateBlogComment(self.session).execute(data)

    def get_blog_comment(self, id: str) -> BlogComment:
        return GetBlogComment(self.session).execute(id)

    # Comment reactions
    def create_comment_reaction(self, data: CommentReactionDTO) -> CommentReaction:
        return CreateCommentReaction(self.session).execute(data)

    def get_comment_reaction(self, id: str) -> CommentReaction:
        return GetCommentReaction(self.session).execute(id)