from tuned.extensions import db
from sqlalchemy.orm import Mapped, mapped_column, relationship, Query
from typing import TYPE_CHECKING, Optional, Any
from tuned.models.base import BaseModel
from tuned.models.tag import sample_tags
from tuned.models.utils import generate_slug

if TYPE_CHECKING:
    from tuned.models.tag import Tag
    from tuned.models.user import User
    from tuned.models.order import Order
    from tuned.models.service import Service

class Sample(BaseModel):
    __tablename__ = 'sample'
    title: Mapped[str] = mapped_column(db.String(200), nullable=False)
    content: Mapped[str] = mapped_column(db.Text, nullable=False)
    excerpt: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    service_id: Mapped[Optional[str]] = mapped_column(db.String(36), db.ForeignKey('service.id'), nullable=True)
    word_count: Mapped[int] = mapped_column(db.Integer, default=0, nullable=False)
    featured: Mapped[bool] = mapped_column(db.Boolean, default=False, nullable=False)
    image: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)
    slug: Mapped[str] = mapped_column(db.String(200), unique=True, nullable=False)
    
    __table_args__ = (
        db.Index('ix_sample_service_featured', 'service_id', 'featured'),
    )
    
    service: Mapped[Optional["Service"]] = relationship("Service", back_populates="samples")
    tag_list: Mapped[list["Tag"]] = relationship('Tag', secondary=sample_tags, lazy='selectin', back_populates='samples')
    
    def __init__(self, **kwargs: Any) -> None:
        super(Sample, self).__init__(**kwargs)
        if not self.slug and self.title:
            self.slug = self.generate_slug(self.title)
    
    @staticmethod
    def generate_slug(title: str) -> str:
        return generate_slug(title, Sample, db.session)
    
    def __repr__(self) -> str:
        return f'<Sample {self.title}>'

class Testimonial(BaseModel):
    __tablename__ = 'testimonial'
    user_id: Mapped[Optional[str]] = mapped_column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    service_id: Mapped[Optional[str]] = mapped_column(db.String(36), db.ForeignKey('service.id'), nullable=True)
    order_id: Mapped[Optional[str]] = mapped_column(db.String(36), db.ForeignKey('order.id'), nullable=True)

    content: Mapped[str] = mapped_column(db.Text, nullable=False)
    rating: Mapped[int] = mapped_column(db.Integer, default=5, nullable=False) # 1-5 rating scale
    is_approved: Mapped[bool] = mapped_column(db.Boolean, default=False, nullable=False)
    
    __table_args__ = (
        db.CheckConstraint('rating >= 1 AND rating <= 5', name='valid_rating'),
    )

    author: Mapped[Optional["User"]] = relationship('User', foreign_keys=[user_id], back_populates='testimonials')
    service: Mapped[Optional["Service"]] = relationship('Service', foreign_keys=[service_id], back_populates='testimonials')
    order: Mapped[Optional["Order"]] = relationship('Order', foreign_keys=[order_id], back_populates='testimonials')

    def __repr__(self) -> str:
        author_name = self.author.username if self.author else "Unknown"
        return f'<Testimonial by {author_name}>'

class FAQ(BaseModel):
    __tablename__ = 'faq'
    question: Mapped[str] = mapped_column(db.String(255), nullable=False)
    answer: Mapped[str] = mapped_column(db.Text, nullable=False)
    category: Mapped[str] = mapped_column(db.String(100), default='General', nullable=False)
    order: Mapped[int] = mapped_column(db.Integer, default=0, nullable=False)
    
    __table_args__ = (
        db.Index('ix_faq_category_order', 'category', 'order'),
    )
    
    def __repr__(self) -> str:
        return f'<FAQ {self.question[:30]}...>'