from tuned.extensions import db
from tuned.models.tag import blog_post_tags
from datetime import datetime, timezone
import re

class BlogCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(120), unique=True, nullable=False)
    description = db.Column(db.Text)
    
    # Relationships
    posts = db.relationship('BlogPost', backref='category', lazy=True)
    
    def __repr__(self):
        return f'<BlogCategory {self.name}>'

class BlogPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(220), unique=True, nullable=False)
    content = db.Column(db.Text, nullable=False)
    excerpt = db.Column(db.Text)
    featured_image = db.Column(db.String(255))
    # Tags now use many-to-many relationship via blog_post_tags table
    # Old column: tags = db.Column(db.String(255))  # Comma-separated tags
    author = db.Column(db.String(100), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('blog_category.id'))
    meta_description = db.Column(db.String(220))
    is_published = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    published_at = db.Column(db.DateTime)
    
    # Table arguments for indexes
    __table_args__ = (
        db.Index('ix_blog_post_published_date', 'is_published', 'published_at'),
    )
    
    # Relationships
    comments = db.relationship('BlogComment', backref='post', lazy=True, cascade='all, delete-orphan')
    tag_list = db.relationship('Tag', secondary=blog_post_tags, lazy='dynamic')
    
    def __init__(self, **kwargs):
        super(BlogPost, self).__init__(**kwargs)
        if not self.slug and self.title:
            self.slug = self.generate_slug(self.title)
    
    @staticmethod
    def generate_slug(title):
        """Generate a unique slug from blog title, handling collisions"""
        base_slug = re.sub(r'[^\w\s-]', '', title.lower())
        base_slug = re.sub(r'[-\s]+', '-', base_slug).strip('-')
        
        slug = base_slug
        counter = 1
        
        # Check for existing slugs and append number if collision detected
        while BlogPost.query.filter_by(slug=slug).first() is not None:
            slug = f"{base_slug}-{counter}"
            counter += 1
            
        return slug
    
    def __repr__(self):
        return f'<BlogPost {self.title}>'

class BlogComment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('blog_post.id'))
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    content = db.Column(db.Text, nullable=False)
    approved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Relationships
    user = db.relationship('User', backref='blog_comments')
    reactions = db.relationship('CommentReaction', backref='comment', lazy='dynamic', cascade='all, delete-orphan')
    
    @property
    def likes_count(self):
        """Get count of 'like' reactions"""
        return self.reactions.filter_by(reaction_type='like').count()
    
    @property
    def dislikes_count(self):
        """Get count of 'dislike' reactions"""
        return self.reactions.filter_by(reaction_type='dislike').count()
    
    def user_reaction(self, user_id=None, ip_address=None):
        """
        Get user's reaction if any.
        
        Args:
            user_id: User ID for authenticated users
            ip_address: IP address for guest users
            
        Returns:
            CommentReaction instance or None
        """
        if user_id:
            return self.reactions.filter_by(user_id=user_id).first()
        elif ip_address:
            return self.reactions.filter_by(ip_address=ip_address).first()
        return None
    
    def to_dict(self):
        """Serialize comment to dictionary"""
        return {
            'id': self.id,
            'content': self.content,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'approved': self.approved,
            'likes_count': self.likes_count,
            'dislikes_count': self.dislikes_count,
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


class CommentReaction(db.Model):
    """
    Track user reactions (like/dislike) on blog comments.
    
    Supports both authenticated users (via user_id) and guests (via ip_address).
    Ensures one reaction per user/IP per comment via unique constraints.
    """
    __tablename__ = 'comment_reaction'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=True)
    comment_id = db.Column(db.Integer, db.ForeignKey('blog_comment.id', ondelete='CASCADE'), nullable=False, index=True)
    reaction_type = db.Column(db.String(10), nullable=False)  # 'like' or 'dislike'
    ip_address = db.Column(db.String(45), nullable=True)  # For guest users (IPv4/IPv6)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Table arguments for constraints and indexes
    __table_args__ = (
        db.Index('ix_reaction_user_comment', 'user_id', 'comment_id'),
        db.Index('ix_reaction_ip_comment', 'ip_address', 'comment_id'),
        db.CheckConstraint("reaction_type IN ('like', 'dislike')", name='check_reaction_type'),
    )
    
    # Relationship
    user = db.relationship('User', backref='comment_reactions')
    
    def to_dict(self):
        """Serialize reaction to dictionary"""
        return {
            'id': self.id,
            'reaction_type': self.reaction_type,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'user_id': self.user_id
        }
    
    def __repr__(self):
        return f'<CommentReaction {self.id} {self.reaction_type}>'
