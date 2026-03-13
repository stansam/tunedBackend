from sqlalchemy.orm import Session
from tuned.models import BlogPost, BlogCategory, BlogComment, CommentReaction
from tuned.repository.blogs.posts import(
    CreateBlog, GetBlogPostBySlug, GetFeaturedBlogPosts
)
from tuned.repository.blogs.categories import(
    CreateBlogCategory, GetBlogCategoryBySlug
)
from tuned.repository.blogs.comments import(
    CreateBlogComment, GetBlogComment
)
from tuned.repository.blogs.reactions import(
    CreateCommentReaction, GetCommentReaction
)
from tuned.dtos import(
    BlogCategoryDTO, BlogCommentDTO, BlogPostDTO, CommentReactionDTO
)
from tuned.extensions import db

class BlogRepository: 
    def __init__(self):
        self.db = db
        self.session = db.session
        
    def create_blog(self, data: BlogPostDTO) -> BlogPost:
        return CreateBlog(self.session).execute(data)
    def get_blog_post_by_slug(self, slug: string) -> BlogPost:
        return GetBlogPostBySlug(self.session).execute(slug)
    def get_featured_blog_posts(self) -> List[BlogPost]:
        return GetFeaturedBlogPosts(self.session).execute()

    
    def create_blog_category(self, data: BlogCategoryDTO) -> BlogCategory:
        return CreateBlogCategory(self.session).execute(data)
    def get_blog_category_by_slug(self, slug: string) -> BlogPost:
        return GetBlogCategoryBySlug(self.session).execute(slug)

    def create_blog_comment(self, data: BlogCommentDTO) -> BlogComment:
        return CreateBlogComment(self.session).execute(data)
    def get_blog_comment(self, id: string) -> BlogComment:
        return GetBlogComment(self.session).execute(id)

    def create_comment_reaction(self, data: BlogCommentReactionDTO) -> CommentReaction:
        return CreateCommentReaction(self.session).execute(data)
    def get_comment_reaction(self, id: string) -> CommentReaction:
        return GetCommentReaction(self.session).execute(id)