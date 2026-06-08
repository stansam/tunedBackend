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
    UpdateOrDeleteBlogCategory, GetBlogCategoryByID
)
from tuned.repository.blogs.comments import (
    CreateBlogComment, GetBlogComment, GetBlogComments,
    UpdateOrDeleteBlogComment,
)
from tuned.repository.blogs.reactions import (
    CreateCommentReaction, GetCommentReaction,
    GetCommentReactions, UpdateOrDeleteCommentReaction
)
from tuned.models.blog import BlogPost, BlogComment, BlogCategory, CommentReaction
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
    def create_blog(self, data: BlogPostDTO) -> BlogPost:
        return CreateBlog(self.session).execute(data)

    def get_blog_post_by_slug(self, slug: str) -> BlogPost:
        return GetBlogPostBySlug(self.session).execute(slug)

    def get_blog_post_by_id(self, id: str) -> BlogPost:
        return GetBlogPostByID(self.session).execute(id)

    def get_featured(self) -> List[BlogPost]:
        return GetFeaturedBlogPosts(self.session).execute()
    
    def get_published(self, req: BlogPostListRequestDTO) -> BlogPostListResponseDTO:
        return GetPublishedBlogPosts(self.session, req).execute()
    
    def update_or_delete_post(self, id: str, data: BlogPostDTO) -> BlogPost:
        return UpdateOrDeleteBlogPost(self.session).execute(id, data)
    
    def get_by_category(self, req: PostByCategoryRequestDTO) -> list[BlogPost]:
        return GetBlogsByCategory(self.session, req).execute()

    # Blog categories
    def create_blog_category(self, data: BlogCategoryDTO) -> BlogCategory:
        return CreateBlogCategory(self.session).execute(data)

    def get_blog_category_by_slug(self, slug: str) -> BlogCategory:
        return GetBlogCategoryBySlug(self.session).execute(slug)
    
    def get_blog_category_by_id(self, id: str) -> BlogCategory:
        return GetBlogCategoryByID(self.session).execute(id)
    
    def list_blog_categories(self) -> List[BlogCategory]:
        return ListBlogCategories(self.session).execute()
    
    def update_or_delete_category(self, id: str, data: BlogCategoryDTO) -> BlogCategory:
        return UpdateOrDeleteBlogCategory(self.session).execute(id, data)

    # Blog comments
    def create_blog_comment(self, data: BlogCommentDTO) -> BlogComment:
        return CreateBlogComment(self.session).execute(data)

    def get_blog_comment(self, id: str) -> BlogComment:
        return GetBlogComment(self.session).execute(id)
    
    def update_or_delete_comment(self, id: str, data: BlogCommentDTO) -> BlogComment:
        return UpdateOrDeleteBlogComment(self.session).execute(id, data)
    
    def get_blog_comments(self, post_id: str) -> List[BlogComment]:
        return GetBlogComments(self.session).execute(post_id)

    # Comment reactions
    def create_comment_reaction(self, data: CommentReactionDTO) -> CommentReaction:
        return CreateCommentReaction(self.session).execute(data)

    def get_comment_reaction(self, id: str) -> CommentReaction:
        return GetCommentReaction(self.session).execute(id)
    
    def get_comment_reactions(self, comment_id: str) -> List[CommentReaction]:
        return GetCommentReactions(self.session).execute(comment_id)
    
    def update_or_delete_comment_reaction(self, id: str, data: CommentReactionDTO) -> CommentReaction:
        return UpdateOrDeleteCommentReaction(self.session).execute(id, data)