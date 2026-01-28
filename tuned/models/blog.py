from app.extensions import db
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
    tags = db.Column(db.String(255))  # Comma-separated tags
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
    
    # Relationship
    user = db.relationship('User', backref='blog_comments')
    
    def __repr__(self):
        return f'<BlogComment {self.id}>'