from sqlalchemy.orm import Mapped
from tuned.models.base import BaseModel
from tuned.models.enums import BlogReactionType
from tuned.models.utils import generate_slug
from tuned.extensions import db
from tuned.models.tag import blog_post_tags
from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tuned.models.user import User

class BlogCategory(BaseModel):
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(120), unique=True, nullable=False)
    description = db.Column(db.Text)
    
    # Relationships
    posts = db.relationship('BlogPost', backref='category', lazy=True)
    
    def __repr__(self):
        return f'<BlogCategory {self.name}>'

class BlogPost(BaseModel):
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(220), unique=True, nullable=False)
    content = db.Column(db.Text, nullable=False)
    excerpt = db.Column(db.Text)
    featured_image = db.Column(db.String(255))
    author = db.Column(db.String(100), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('blog_category.id'))
    meta_description = db.Column(db.String(220))
    is_published = db.Column(db.Boolean, default=False)
    is_featured = db.Column(db.Boolean, default=False)
    published_at = db.Column(db.DateTime)
    
    # Table arguments for indexes
    __table_args__ = (
        db.Index('ix_blog_post_published_date', 'is_published', 'published_at'),
    )
    
    # Relationships
    comments = db.relationship('BlogComment', foreign_keys="BlogComment.post_id", backref='post', lazy=True, cascade='all, delete-orphan')
    tag_list = db.relationship('Tag', secondary=blog_post_tags, lazy='dynamic', back_populates='blog_posts')
    
    def __init__(self, **kwargs):
        super(BlogPost, self).__init__(**kwargs)
        if not self.slug and self.title:
            self.slug = self.generate_slug(self.title)
    
    @staticmethod
    def generate_slug(title):
        return generate_slug(title, BlogPost, db.session)
    
    def __repr__(self):
        return f'<BlogPost {self.title}>'

class BlogComment(BaseModel):
    post_id = db.Column(db.String(36), db.ForeignKey('blog_post.id'))
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    content = db.Column(db.Text, nullable=False)
    approved = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Relationships
    user: Mapped["User"] = db.relationship('User', foreign_keys=[user_id], backref='blog_comments')
    reactions: Mapped["CommentReaction"] = db.relationship('CommentReaction', foreign_keys="CommentReaction.comment_id", backref='comment', lazy='dynamic', cascade='all, delete-orphan')
    
    @property
    def total_likes(self) -> int:
        # return self.reactions.filter_by(reaction_type='like').count()
        return sum(
            1 for r in self.reactions
            if r.reaction_type == BlogReactionType.LIKE
        )
    
    @property
    def total_dislikes(self) -> int:
        # return self.reactions.filter_by(reaction_type='dislike').count()
        return sum(
            1 for r in self.reactions
            if r.reaction_type == BlogReactionType.DISLIKE
        )
    
    def user_reaction(self, user_id=None, ip_address=None) -> "CommentReaction" | None:
        if user_id:
            return self.reactions.filter_by(user_id=user_id).first()
        elif ip_address:
            return self.reactions.filter_by(ip_address=ip_address).first()
        return None
    
    def to_dict(self):
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
    
    def __repr__(self):
        return f'<BlogComment {self.id}>'


class CommentReaction(BaseModel):
    __tablename__ = 'comment_reaction'
    
    user_id = db.Column(db.String(36), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=True)
    comment_id = db.Column(db.String(36), db.ForeignKey('blog_comment.id', ondelete='CASCADE'), nullable=False, index=True)
    reaction_type = db.Column(db.Enum(BlogReactionType), nullable=False)  # 'like' or 'dislike'
    ip_address = db.Column(db.String(45), nullable=True)  # For guest users (IPv4/IPv6)
    
    __table_args__ = (
        db.Index('ix_reaction_user_comment', 'user_id', 'comment_id'),
        db.Index('ix_reaction_ip_comment', 'ip_address', 'comment_id'),
        db.CheckConstraint("reaction_type IN ('like', 'dislike')", name='check_reaction_type'),
    )
    
    # Relationship
    user: Mapped["User"]  = db.relationship('User', foreign_keys=[user_id], backref='comment_reactions')
    
    def to_dict(self):
        return {
            'id': self.id,
            'reaction_type': self.reaction_type,
            'created_at': self.created_at.isoformat(),
            'user_id': self.user_id
        }
    
    def __repr__(self):
        return f'<CommentReaction {self.id} {self.reaction_type}>'
