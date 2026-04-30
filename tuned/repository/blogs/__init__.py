# from tuned.dtos.blogs import CommentReactionResponseDTO, BlogCommentResponseDTO
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from tuned.repository.blogs.posts import (
    CreateBlog, GetBlogPostBySlug, GetBlogsByCategory,
    GetFeaturedBlogPosts, GetPublishedBlogPosts,
    UpdateOrDeleteBlogPost, GetBlogPostByID,
)
from tuned.repository.blogs.categories import (
    CreateBlogCategory, GetBlogCategoryBySlug, ListBlogCategories,
    UpdateOrDeleteBlogCategory
)
from tuned.repository.blogs.comments import (
    CreateBlogComment, GetBlogComment, GetBlogComments,
    UpdateOrDeleteBlogComment
)
from tuned.repository.blogs.reactions import (
    CreateCommentReaction, GetCommentReaction,
    GetCommentReactions, UpdateOrDeleteCommentReaction
)
from tuned.dtos import (
    BlogCategoryDTO, BlogCommentDTO,
    BlogPostDTO, CommentReactionDTO, BlogPostListRequestDTO,
    BlogPostResponseDTO, BlogCategoryResponseDTO,
    BlogCommentResponseDTO, CommentReactionResponseDTO,
    PostByCategoryRequestDTO, BlogPostListResponseDTO
)
from tuned.extensions import db


from tuned.repository.protocols import BlogRepositoryProtocol

class BlogRepository(BlogRepositoryProtocol):
    def __init__(self, session: Session) -> None:
        self.session = session

    # Blog posts
    def create_blog(self, data: BlogPostDTO) -> BlogPostResponseDTO:
        return CreateBlog(self.session).execute(data)

    def get_blog_post_by_slug(self, slug: str) -> BlogPostResponseDTO:
        return GetBlogPostBySlug(self.session).execute(slug)

    def get_blog_post_by_id(self, id: str) -> BlogPostResponseDTO:
        return GetBlogPostByID(self.session).execute(id)

    def get_featured(self) -> List[BlogPostResponseDTO]:
        return GetFeaturedBlogPosts(self.session).execute()
    
    def get_published(self, req: BlogPostListRequestDTO) -> BlogPostListResponseDTO:
        return GetPublishedBlogPosts(self.session, req).execute()
    
    def update_or_delete_post(self, id: str, data: BlogPostDTO) -> BlogPostResponseDTO:
        return UpdateOrDeleteBlogPost(self.session).execute(id, data)
    
    def get_by_category(self, req: PostByCategoryRequestDTO) -> list[BlogPostResponseDTO]:
        return GetBlogsByCategory(self.session, req).execute()

    # Blog categories
    def create_blog_category(self, data: BlogCategoryDTO) -> BlogCategoryResponseDTO:
        return CreateBlogCategory(self.session).execute(data)

    def get_blog_category_by_slug(self, slug: str) -> BlogCategoryResponseDTO:
        return GetBlogCategoryBySlug(self.session).execute(slug)
    
    def list_blog_categories(self) -> List[BlogCategoryResponseDTO]:
        return ListBlogCategories(self.session).execute()
    
    def update_or_delete_category(self, id: str, data: BlogCategoryDTO) -> BlogCategoryResponseDTO:
        return UpdateOrDeleteBlogCategory(self.session).execute(id, data)

    # Blog comments
    def create_blog_comment(self, data: BlogCommentDTO) -> BlogCommentResponseDTO:
        return CreateBlogComment(self.session).execute(data)

    def get_blog_comment(self, id: str) -> BlogCommentResponseDTO:
        return GetBlogComment(self.session).execute(id)
    
    def update_or_delete_comment(self, id: str, data: BlogCommentDTO) -> BlogCommentResponseDTO:
        return UpdateOrDeleteBlogComment(self.session).execute(id, data)
    
    def get_blog_comments(self, post_id: str) -> List[BlogCommentResponseDTO]:
        return GetBlogComments(self.session).execute(post_id)

    # Comment reactions
    def create_comment_reaction(self, data: CommentReactionDTO) -> CommentReactionResponseDTO:
        return CreateCommentReaction(self.session).execute(data)

    def get_comment_reaction(self, id: str) -> CommentReactionResponseDTO:
        return GetCommentReaction(self.session).execute(id)
    
    def get_comment_reactions(self, comment_id: str) -> List[CommentReactionResponseDTO]:
        return GetCommentReactions(self.session).execute(comment_id)
    
    def update_or_delete_comment_reaction(self, id: str, data: CommentReactionDTO) -> CommentReactionResponseDTO:
        return UpdateOrDeleteCommentReaction(self.session).execute(id, data)