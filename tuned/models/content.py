from app.extensions import db
from datetime import datetime, timezone
import re

class Sample(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    excerpt = db.Column(db.Text)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'))
    word_count = db.Column(db.Integer, default=0)
    featured = db.Column(db.Boolean, default=False)
    tags = db.Column(db.String(255), nullable=True) 
    image = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    slug = db.Column(db.String(200), unique=True, nullable=False)
    
    # Table arguments for indexes
    __table_args__ = (
        db.Index('ix_sample_service_featured', 'service_id', 'featured'),
    )
    
    def __init__(self, **kwargs):
        super(Sample, self).__init__(**kwargs)
        if not self.slug and self.title:
            self.slug = self.generate_slug(self.title)
    
    @staticmethod
    def generate_slug(title):
        """Generate a unique slug from sample title, handling collisions"""
        base_slug = re.sub(r'[^\w\s-]', '', title.lower())
        base_slug = re.sub(r'[-\s]+', '-', base_slug).strip('-')
        
        slug = base_slug
        counter = 1
        
        # Check for existing slugs and append number if collision detected
        while Sample.query.filter_by(slug=slug).first() is not None:
            slug = f"{base_slug}-{counter}"
            counter += 1
            
        return slug
    
    def __repr__(self):
        return f'<Sample {self.title}>'

class Testimonial(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'))
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'))

    content = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, default=5) # 1-5 rating scale
    is_approved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    __table_args__ = (
        db.CheckConstraint('rating >= 1 AND rating <= 5', name='valid_rating'),
    )

    def __repr__(self):
        return f'<Testimonial by {self.user.username}>'

class FAQ(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(255), nullable=False)
    answer = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100), default='General')
    order = db.Column(db.Integer, default=0)
    
    # Table arguments for indexes
    __table_args__ = (
        db.Index('ix_faq_category_order', 'category', 'order'),
    )
    
    def __repr__(self):
        return f'<FAQ {self.question[:30]}...>'