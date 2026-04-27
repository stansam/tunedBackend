from tuned.extensions import db
from tuned.models.base import BaseModel
from tuned.models.utils import generate_slug
from tuned.models.tag import service_tags
# from datetime import datetime
from typing import TYPE_CHECKING, Optional, Any
from sqlalchemy.orm import Mapped, mapped_column, relationship #, Query

if TYPE_CHECKING:
    from tuned.models.order import Order
    from tuned.models.content import Testimonial, Sample
    from tuned.models.price import PricingCategory, PriceRate
    from tuned.models.tag import Tag

class ServiceCategory(BaseModel):
    __tablename__ = 'service_category'
    name: Mapped[str] = mapped_column(db.String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    order: Mapped[int] = mapped_column(db.Integer, default=0, nullable=False)
    
    services: Mapped[list["Service"]] = relationship('Service', back_populates='category', lazy=True, cascade='all, delete-orphan')

    def __init__(self, **kwargs: Any) -> None:
        super(ServiceCategory, self).__init__(**kwargs)
    
    def __repr__(self) -> str:
        return f'<ServiceCategory {self.name}>'
    def to_dict(self) -> dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'order': self.order
        }

class Service(BaseModel):
    __tablename__ = 'service'
    name: Mapped[str] = mapped_column(db.String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    category_id: Mapped[str] = mapped_column(db.String(36), db.ForeignKey('service_category.id'), nullable=False)
    featured: Mapped[bool] = mapped_column(db.Boolean, default=False, nullable=False)
    pricing_category_id: Mapped[str] = mapped_column(db.String(36), db.ForeignKey('pricing_category.id'), nullable=False)
    slug: Mapped[str] = mapped_column(db.String(200), unique=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(db.Boolean, default=True, server_default='true', nullable=False)
    
    __table_args__ = (
        db.Index('ix_service_category_featured', 'category_id', 'featured'),
    )
    
    category: Mapped["ServiceCategory"] = relationship("ServiceCategory", back_populates="services")
    orders: Mapped[list["Order"]] = relationship('Order', back_populates='service', lazy=True)
    samples: Mapped[list["Sample"]] = relationship('Sample', back_populates='service', lazy=True)
    testimonials: Mapped[list["Testimonial"]] = relationship('Testimonial', back_populates='service', lazy=True)
    pricing_category: Mapped["PricingCategory"] = relationship('PricingCategory', back_populates='service')
    tag_list: Mapped[list["Tag"]] = relationship('Tag', secondary=service_tags, lazy='selectin', back_populates='services')
    
    def __init__(self, **kwargs: Any) -> None:
        super(Service, self).__init__(**kwargs)
        if not self.slug and self.name:
            self.slug = self.generate_slug(self.name)
    
    @staticmethod
    def generate_slug(name: str) -> str:
        return generate_slug(name, Service, db.session)
    
    def __repr__(self) -> str:
        return f'<Service {self.name}>'
    def to_dict(self) -> dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'category_id': self.category_id,
            'featured': self.featured,
            'tags': self.get_tags(),
            'pricing_category_id': self.pricing_category_id
        }
    def get_tags(self) -> list[str]:
        if self.tag_list:
            return [tag.name for tag in self.tag_list]
        return []

class AcademicLevel(BaseModel):
    __tablename__ = 'academic_level'
    name: Mapped[str] = mapped_column(db.String(100), nullable=False)
    order: Mapped[int] = mapped_column(db.Integer, default=0, nullable=False)
    
    orders: Mapped[list["Order"]] = relationship('Order', back_populates='academic_level', lazy=True)
    price_rates: Mapped[list["PriceRate"]] = relationship('PriceRate', back_populates='academic_level', lazy=True)

    def __repr__(self) -> str:
        return f'<AcademicLevel {self.name}>'
    def to_dict(self) -> dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'order': self.order
        }
    

class Deadline(BaseModel):
    __tablename__ = 'deadline'
    name: Mapped[str] = mapped_column(db.String(100), nullable=False)
    hours: Mapped[int] = mapped_column(db.Integer, nullable=False)
    order: Mapped[int] = mapped_column(db.Integer, default=0, nullable=False)
    
    __table_args__ = (
        db.CheckConstraint('hours > 0 AND hours <= 720', name='valid_deadline_hours'),
    )
    
    orders: Mapped[list["Order"]] = relationship('Order', back_populates='deadline', lazy=True)
    price_rates: Mapped[list["PriceRate"]] = relationship('PriceRate', back_populates='deadline', lazy=True)
    
    def __repr__(self) -> str:
        return f'<Deadline {self.name}>'
    def to_dict(self) -> dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'hours': self.hours,
            'order': self.order
        }