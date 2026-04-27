from sqlalchemy.orm import Mapped, mapped_column, relationship
from tuned.models.base import BaseModel
from tuned.models.enums import BlogReactionType
from tuned.models.utils import generate_slug
from tuned.extensions import db
from tuned.models.tag import blog_post_tags
from typing import TYPE_CHECKING, Optional, Any
from datetime import datetime

if TYPE_CHECKING:
    from tuned.models.user import User
    from tuned.models.tag import Tag

class BlogCategory(BaseModel):
    __tablename__ = 'blog_category'
    name: Mapped[str] = mapped_column(db.String(100), nullable=False)
    slug: Mapped[str] = mapped_column(db.String(120), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    
    # Relationships
    posts: Mapped[list["BlogPost"]] = relationship('BlogPost', back_populates='category', lazy=True)
    
    def __repr__(self) -> str:
        return f'<BlogCategory {self.name}>'

class BlogPost(BaseModel):
    __tablename__ = 'blog_post'
    title: Mapped[str] = mapped_column(db.String(200), nullable=False)
    slug: Mapped[str] = mapped_column(db.String(220), unique=True, nullable=False)
    content: Mapped[str] = mapped_column(db.Text, nullable=False)
    excerpt: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    featured_image: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)
    author: Mapped[str] = mapped_column(db.String(100), nullable=False)
    category_id: Mapped[Optional[str]] = mapped_column(db.String(36), db.ForeignKey('blog_category.id'), nullable=True)
    meta_description: Mapped[Optional[str]] = mapped_column(db.String(220), nullable=True)
    is_published: Mapped[bool] = mapped_column(db.Boolean, default=False, nullable=False)
    is_featured: Mapped[bool] = mapped_column(db.Boolean, default=False, nullable=False)
    published_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True)
    
    __table_args__ = (
        db.Index('ix_blog_post_published_date', 'is_published', 'published_at'),
    )
    
    category: Mapped[Optional["BlogCategory"]] = relationship("BlogCategory", back_populates="posts")
    comments: Mapped[list["BlogComment"]] = relationship('BlogComment', foreign_keys="BlogComment.post_id", back_populates='post', lazy=True, cascade='all, delete-orphan')
    tag_list: Mapped[list["Tag"]] = relationship('Tag', secondary=blog_post_tags, lazy='selectin', back_populates='blog_posts')
    
    def __init__(self, **kwargs: Any) -> None:
        super(BlogPost, self).__init__(**kwargs)
        if not self.slug and self.title:
            self.slug = self.generate_slug(self.title)
    
    @staticmethod
    def generate_slug(title: str) -> str:
        return generate_slug(title, BlogPost, db.session)
    
    def __repr__(self) -> str:
        return f'<BlogPost {self.title}>'

class BlogComment(BaseModel):
    __tablename__ = 'blog_comment'
    post_id: Mapped[Optional[str]] = mapped_column(db.String(36), db.ForeignKey('blog_post.id'), nullable=True)
    name: Mapped[Optional[str]] = mapped_column(db.String(100), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(db.String(100), nullable=True)
    content: Mapped[str] = mapped_column(db.Text, nullable=False)
    approved: Mapped[bool] = mapped_column(db.Boolean, default=False, nullable=False)
    user_id: Mapped[Optional[str]] = mapped_column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    
    # Relationships
    post: Mapped[Optional["BlogPost"]] = relationship('BlogPost', foreign_keys=[post_id], back_populates='comments')
    user: Mapped[Optional["User"]] = relationship('User', foreign_keys=[user_id], back_populates='blog_comments')
    reactions: Mapped[list["CommentReaction"]] = relationship('CommentReaction', foreign_keys="CommentReaction.comment_id", back_populates='comment', lazy='selectin', cascade='all, delete-orphan')
    
    @property
    def total_likes(self) -> int:
        return sum(
            1 for r in self.reactions
            if r.reaction_type == BlogReactionType.LIKE
        )
    
    @property
    def total_dislikes(self) -> int:
        return sum(
            1 for r in self.reactions
            if r.reaction_type == BlogReactionType.DISLIKE
        )
    
    def to_dict(self) -> dict[str, Any]:
        return {
            'id': self.id,
            'content': self.content,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'approved': self.approved,
            'total_likes': self.total_likes,
            'total_dislikes': self.total_dislikes,
            'user': {
                'id': self.user.id,
                'name': self.user.get_name(),
                'profile_pic': self.user.profile_pic
            } if self.user else {
                'name': self.name,
                'email': self.email
            }
        }
    
    def __repr__(self) -> str:
        return f'<BlogComment {self.id}>'


class CommentReaction(BaseModel):
    __tablename__ = 'comment_reaction'
    
    user_id: Mapped[Optional[str]] = mapped_column(db.String(36), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=True)
    comment_id: Mapped[str] = mapped_column(db.String(36), db.ForeignKey('blog_comment.id', ondelete='CASCADE'), nullable=False, index=True)
    reaction_type: Mapped[BlogReactionType] = mapped_column(db.Enum(BlogReactionType), nullable=False)  # 'like' or 'dislike'
    ip_address: Mapped[Optional[str]] = mapped_column(db.String(45), nullable=True)  # For guest users (IPv4/IPv6)
    
    __table_args__ = (
        db.Index('ix_reaction_user_comment', 'user_id', 'comment_id'),
        db.Index('ix_reaction_ip_comment', 'ip_address', 'comment_id'),
        db.CheckConstraint("reaction_type IN ('like', 'dislike')", name='check_reaction_type'),
    )
    
    # Relationship
    comment: Mapped["BlogComment"] = relationship("BlogComment", foreign_keys=[comment_id], back_populates="reactions")
    user: Mapped[Optional["User"]] = relationship('User', foreign_keys=[user_id], back_populates='comment_reactions')
    
    def to_dict(self) -> dict[str, Any]:
        return {
            'id': self.id,
            'reaction_type': self.reaction_type.value,
            'created_at': self.created_at.isoformat(),
            'user_id': self.user_id
        }
    
    def __repr__(self) -> str:
        return f'<CommentReaction {self.id} {self.reaction_type}>'
