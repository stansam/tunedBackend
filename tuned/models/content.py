from tuned.extensions import db
from tuned.models.base import BaseModel
from tuned.models.tag import sample_tags
from tuned.models.utils import generate_slug
from datetime import datetime, timezone
import re

class Sample(BaseModel):
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    excerpt = db.Column(db.Text)
    service_id = db.Column(db.String(36), db.ForeignKey('service.id'))
    word_count = db.Column(db.Integer, default=0)
    featured = db.Column(db.Boolean, default=False)
    image = db.Column(db.String(255))
    slug = db.Column(db.String(200), unique=True, nullable=False)
    
    __table_args__ = (
        db.Index('ix_sample_service_featured', 'service_id', 'featured'),
    )
    
    tag_list = db.relationship('Tag', secondary=sample_tags, lazy='dynamic', back_populates='samples')
    
    def __init__(self, **kwargs):
        super(Sample, self).__init__(**kwargs)
        if not self.slug and self.title:
            self.slug = self.generate_slug(self.title)
    
    @staticmethod
    def generate_slug(title):
        return generate_slug(title, Sample, db.session)
    
    def __repr__(self):
        return f'<Sample {self.title}>'

class Testimonial(BaseModel):
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'))
    service_id = db.Column(db.String(36), db.ForeignKey('service.id'))
    order_id = db.Column(db.String(36), db.ForeignKey('order.id'))

    content = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, default=5) # 1-5 rating scale
    is_approved = db.Column(db.Boolean, default=False)
    
    __table_args__ = (
        db.CheckConstraint('rating >= 1 AND rating <= 5', name='valid_rating'),
    )

    def __repr__(self):
        return f'<Testimonial by {self.user.username}>'

class FAQ(BaseModel):
    question = db.Column(db.String(255), nullable=False)
    answer = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100), default='General')
    order = db.Column(db.Integer, default=0)
    
    __table_args__ = (
        db.Index('ix_faq_category_order', 'category', 'order'),
    )
    
    def __repr__(self):
        return f'<FAQ {self.question[:30]}...>'