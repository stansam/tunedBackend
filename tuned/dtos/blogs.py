from typing import Optional

class BlogCategoryDTO:
    name: str
    slug: str
    description: str

class BlogPostDTO:
    title: str
    slug: str
    content: str
    excerpt: str
    featured_image: str
    author: str
    category_id: str
    meta_description: str
    is_published: Optional[bool] = False
    is_featured: Optional[bool] = False
    published_at: Optional[str] = None

class BlogCommentDTO:
    post_id: str
    name: str
    email: str
    content: str
    user_id: str
    approved: Optional[bool] = False 

class CommentReactionDTO:
    user_id: str
    comment_id: str
    reaction_type: str
    ip_address: Optional[str] = None