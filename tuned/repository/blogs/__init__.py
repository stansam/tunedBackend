from sqlalchemy.orm import Session
from tuned.models import BlogPost, BlogCategory, BlogComment, CommentReaction
from tuned.repository.blogs.create import(
    CreateBlog, CreateBlogCategory, CreateBlogComment, CreateCommentReaction
)
from tuned.repository.blogs.get import(
    GetBlogCategoryBySlug, GetBlogPostBySlug,
    GetBlogComment, GetCommentReaction
)
from tuned.dtos.blogs import(
    BlogCategoryDTO, BlogCommentDTO, BlogPostDTO, CommentReactionDTO
)
from tuned.extensions import db

class BlogRepository: 
    def __init__(self):
        self.db = db  
    def create_blog(self, data: BlogPostDTO) -> BlogPost:
        return CreateBlog(self.db).execute(data)
    def create_blog_category(self, data: BlogCategoryDTO) -> BlogCategory:
        return CreateBlogCategory(self.db).execute(data)
    def create_blog_comment(self, data: BlogCommentDTO) -> BlogComment:
        return CreateBlogComment(self.db).execute(data)
    def create_comment_reaction(self, data: BlogCommentReactionDTO) -> CommentReaction:
        return CreateCommentReaction(self.db).execute(data)

    
    def get_blog_post_by_slug(self, slug: string) -> BlogPost:
        return GetBlogPostBySlug(self.db).execute(slug)
    def get_blog_category_by_slug(self, slug: string) -> BlogPost:
        return GetBlogCategoryBySlug(self.db).execute(slug)
    def get_blog_comment(self, id: string) -> BlogComment:
        return GetBlogComment(self.db).execute(id)
    def get_comment_reaction(self, id: string) -> CommentReaction:
        return GetCommentReaction(self.db).execute(id)