from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class BlogCategoryDTO:
    name: str
    slug: str
    description: str 


@dataclass
class BlogPostDTO:
    title: str
    content: str
    author: str
    category_id: str
    slug: Optional[str] = None
    excerpt: str = ""
    featured_image: str = ""
    meta_description: str = ""
    is_published: bool = False
    is_featured: bool = False
    published_at: Optional[datetime] = None

@dataclass
class BlogPostResponseDTO:
    id: str
    title: str
    content: str
    author: str
    category_id: str
    slug: str
    excerpt: str
    featured_image: str
    meta_description: str
    is_published: bool
    is_featured: bool
    published_at: str

    @classmethod
    def from_model(cls, obj) -> "BlogPostResponseDTO":
        return cls(
            id=obj.id,
            title=obj.title,
            content=obj.content,
            author=obj.author,
            category_id=obj.category_id,
            slug=obj.slug,
            excerpt=obj.excerpt or "",
            featured_image=obj.featured_image or "",
            meta_description=obj.meta_description or "",
            is_published=obj.is_published,
            is_featured=obj.is_featured,
            published_at=obj.published_at.isoformat() if obj.published_at else "",
        )


@dataclass
class BlogCommentDTO:
    post_id: str
    content: str
    name: str = ""
    email: str = ""
    user_id: Optional[str] = None
    approved: bool = False


@dataclass
class CommentReactionDTO:
    comment_id: str
    reaction_type: str
    user_id: Optional[str] = None
    ip_address: Optional[str] = None