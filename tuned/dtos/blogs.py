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
class BlogCommentResponseDTO:
    id: str
    post_id: str
    content: str
    name: str = ""
    email: str = ""
    user_id: Optional[str] = None
    approved: bool = False

    @classmethod
    def from_model(cls, obj) -> "BlogCommentResponseDTO":
        return cls(
            id=str(obj.id),
            post_id=str(obj.post_id),
            content=obj.content,
            name=obj.name,
            email=obj.email,
            user_id=str(obj.user_id),
            approved=obj.approved,
        )


@dataclass
class CommentReactionDTO:
    comment_id: str
    reaction_type: str
    user_id: Optional[str] = None
    ip_address: Optional[str] = None

@dataclass
class CommentReactionResponseDTO:
    id: str
    comment_id: str
    reaction_type: str
    user_id: Optional[str] = None
    ip_address: Optional[str] = None

    @classmethod
    def from_model(cls, obj) -> "CommentReactionResponseDTO":
        return cls(
            id=str(obj.id),
            comment_id=str(obj.comment_id),
            reaction_type=obj.reaction_type,
            user_id=str(obj.user_id),
            ip_address=obj.ip_address,
        )