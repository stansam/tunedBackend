from tuned.extensions import db
from tuned.models.base import BaseModel
from tuned.models.utils import generate_slug
from tuned.models.tag import service_tags
from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy.orm import Mapped, Query
if TYPE_CHECKING:
    from tuned.models.order import Order
    from tuned.models.content import Testimonial, Sample
    from tuned.models.price import PricingCategory, PriceRate
    from tuned.models.tag import Tag

class ServiceCategory(BaseModel):
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    order = db.Column(db.Integer, default=0)
    
    services: Mapped[list["Service"]] = db.relationship('Service', backref='category', lazy=True, cascade='all, delete-orphan')

    def __init__(self, **kwargs):
        super(ServiceCategory, self).__init__(**kwargs)
    
    def __repr__(self):
        return f'<ServiceCategory {self.name}>'
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'order': self.order
        }

class Service(BaseModel):
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    category_id = db.Column(db.String(36), db.ForeignKey('service_category.id'))
    featured = db.Column(db.Boolean, default=False)
    pricing_category_id = db.Column(db.Integer, db.ForeignKey('pricing_category.id'))
    slug = db.Column(db.String(200), unique=True, nullable=False)
    is_active = db.Column(db.Boolean, default=True, server_default='true')
    
    # Table arguments for indexes
    __table_args__ = (
        db.Index('ix_service_category_featured', 'category_id', 'featured'),
    )
    
    orders: Mapped[list["Order"]] = db.relationship('Order', back_populates='service', lazy=True)
    samples: Mapped[list["Sample"]] = db.relationship('Sample', backref='service', lazy=True)
    testimonials: Mapped[list["Testimonial"]] = db.relationship('Testimonial', backref='service', lazy=True)
    pricing_category: Mapped["PricingCategory"] = db.relationship('PricingCategory', back_populates='service')
    tag_list: Mapped[Query["Tag"]] = db.relationship('Tag', secondary=service_tags, lazy='dynamic', back_populates='services')
    
    def __init__(self, **kwargs):
        super(Service, self).__init__(**kwargs)
        if not self.slug and self.name:
            self.slug = self.generate_slug(self.name)
    
    @staticmethod
    def generate_slug(name):
        return generate_slug(name, Service, db.session)
    
    def __repr__(self):
        return f'<Service {self.name}>'
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'category_id': self.category_id,
            'featured': self.featured,
            'tags': self.get_tags(),
            'pricing_category_id': self.pricing_category_id
        }
    def get_tags(self):
        if self.tag_list:
            return [tag.name for tag in self.tag_list]
        return []

class AcademicLevel(BaseModel):
    name = db.Column(db.String(100), nullable=False)
    order = db.Column(db.Integer, default=0)
    
    orders: Mapped[list["Order"]] = db.relationship('Order', back_populates='academic_level', lazy=True)
    price_rates: Mapped[list["PriceRate"]] = db.relationship('PriceRate', backref='academic_level', lazy=True)

    def __repr__(self):
        return f'<AcademicLevel {self.name}>'
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'order': self.order
        }
    

class Deadline(BaseModel):
    name = db.Column(db.String(100), nullable=False)
    hours = db.Column(db.Integer, nullable=False)
    order = db.Column(db.Integer, default=0)
    
    # Table arguments for constraints
    __table_args__ = (
        db.CheckConstraint('hours > 0 AND hours <= 720', name='valid_deadline_hours'),
    )
    
    orders: Mapped[list["Order"]] = db.relationship('Order', back_populates='deadline', lazy=True)
    price_rates: Mapped[list["PriceRate"]] = db.relationship('PriceRate', backref='deadline', lazy=True)
    
    def __repr__(self):
        return f'<Deadline {self.name}>'
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'hours': self.hours,
            'order': self.order
        }