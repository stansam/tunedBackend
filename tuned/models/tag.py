"""
Tag model for normalized tag management across services, samples, and blog posts.
Replaces comma-separated tag strings with proper many-to-many relationships.
"""
from app.extensions import db
from datetime import datetime, timezone


# Association tables for many-to-many relationships
service_tags = db.Table('service_tags',
    db.Column('service_id', db.Integer, db.ForeignKey('service.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True),
    db.Column('created_at', db.DateTime, default=lambda: datetime.now(timezone.utc))
)

sample_tags = db.Table('sample_tags',
    db.Column('sample_id', db.Integer, db.ForeignKey('sample.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True),
    db.Column('created_at', db.DateTime, default=lambda: datetime.now(timezone.utc))
)

blog_post_tags = db.Table('blog_post_tags',
    db.Column('blog_post_id', db.Integer, db.ForeignKey('blog_post.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True),
    db.Column('created_at', db.DateTime, default=lambda: datetime.now(timezone.utc))
)


class Tag(db.Model):
    """Normalized tag model for services, samples, and blog posts"""
    __tablename__ = 'tag'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False, index=True)
    slug = db.Column(db.String(60), unique=True, nullable=False, index=True)
    description = db.Column(db.String(200))
    usage_count = db.Column(db.Integer, default=0)  # Denormalized count for performance
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships with backref
    services = db.relationship('Service', secondary=service_tags, backref=db.backref('tag_objects', lazy='dynamic'))
    samples = db.relationship('Sample', secondary=sample_tags, backref=db.backref('tag_objects', lazy='dynamic'))
    blog_posts = db.relationship('BlogPost', secondary=blog_post_tags, backref=db.backref('tag_objects', lazy='dynamic'))
    
    def __init__(self, name, description=None):
        self.name = name.strip().lower()
        self.slug = self.name.replace(' ', '-')
        self.description = description
    
    def increment_usage(self):
        """Increment usage count when tag is applied"""
        self.usage_count += 1
        db.session.commit()
    
    def decrement_usage(self):
        """Decrement usage count when tag is removed"""
        if self.usage_count > 0:
            self.usage_count -= 1
            db.session.commit()
    
    @staticmethod
    def get_or_create(tag_name):
        """Get existing tag or create new one"""
        tag = Tag.query.filter_by(name=tag_name.strip().lower()).first()
        if not tag:
            tag = Tag(name=tag_name)
            db.session.add(tag)
            db.session.commit()
        return tag
    
    @staticmethod
    def parse_tags(tag_string):
        """Parse comma-separated tag string into Tag objects"""
        if not tag_string:
            return []
        
        tag_names = [t.strip() for t in tag_string.split(',') if t.strip()]
        tags = []
        for name in tag_names:
            tag = Tag.get_or_create(name)
            tags.append(tag)
        return tags
    
    def __repr__(self):
        return f'<Tag {self.name}>'
