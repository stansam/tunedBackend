from tuned.extensions import db
from tuned.models.base import BaseModel
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING, Optional, Any

if TYPE_CHECKING:
    from tuned.models.service import Service, AcademicLevel, Deadline
    from tuned.models.audit import PriceHistory

class PricingCategory(BaseModel):
    __tablename__ = 'pricing_category'
    name: Mapped[str] = mapped_column(db.String(100), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    display_order: Mapped[int] = mapped_column(db.Integer, default=0, nullable=False)
    
    # Relationships
    service: Mapped[list["Service"]] = relationship('Service', back_populates='pricing_category', lazy=True)
    price_rates: Mapped[list["PriceRate"]] = relationship('PriceRate', back_populates='pricing_category', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f'<PricingCategory {self.name}>'
    
    def to_dict(self) -> dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'display_order': self.display_order
        }

class PriceRate(BaseModel):
    __tablename__ = 'price_rate'
    pricing_category_id: Mapped[str] = mapped_column(db.String(36), db.ForeignKey('pricing_category.id'), nullable=False)
    academic_level_id: Mapped[str] = mapped_column(db.String(36), db.ForeignKey('academic_level.id'), nullable=False)
    deadline_id: Mapped[str] = mapped_column(db.String(36), db.ForeignKey('deadline.id'), nullable=False)
    price_per_page: Mapped[float] = mapped_column(db.Float, nullable=False)
    is_active: Mapped[bool] = mapped_column(db.Boolean, default=True, server_default='true', nullable=False)
    
    __table_args__ = (
        db.UniqueConstraint('pricing_category_id', 'academic_level_id', 'deadline_id'),
        db.Index('ix_price_rate_lookup', 'pricing_category_id', 'academic_level_id', 'deadline_id'),
        db.CheckConstraint('price_per_page > 0 AND price_per_page < 10000', name='valid_price'),
    )
    
    pricing_category: Mapped["PricingCategory"] = relationship("PricingCategory", back_populates="price_rates")
    academic_level: Mapped["AcademicLevel"] = relationship("AcademicLevel", back_populates="price_rates")
    deadline: Mapped["Deadline"] = relationship("Deadline", back_populates="price_rates")
    price_history: Mapped[list["PriceHistory"]] = relationship("PriceHistory", back_populates="price_rate", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f'<PriceRate for Category {self.pricing_category_id}, Level {self.academic_level_id}, Deadline {self.deadline_id}>'
