from dataclasses import dataclass
from typing import Optional
from tuned.models import Service
from tuned.utils.enums import PricingCategoryEnum
from tuned.dtos.price import PricingCategoryResponseDTO

@dataclass
class ServiceDTO:
    name: str
    description: str
    category_id: str
    featured: bool
    pricing_category_id: str
    slug: Optional[str] = None
    is_active: Optional[bool] = True


@dataclass
class ServiceCategoryDTO:
    name: str
    description: str = ""
    order: int = 0


@dataclass
class ServiceWithPricingCategory:
  id: str
  name: str
  category: str # Service category name
  pricing_category: PricingCategoryEnum # Pricing category name


@dataclass
class ServiceResponseDTO:
    id: str
    name: str
    description: str
    category_id: str
    featured: bool
    pricing_category_id: str
    slug: str
    is_active: bool
    category: Optional[ServiceCategoryResponseDTO] = None
    pricing_category: Optional[PricingCategoryResponseDTO] = None

    @classmethod
    def from_model(cls, model: Service) -> "ServiceResponseDTO":
        return cls(
            id=model.id,
            name=model.name,
            description=model.description,
            category_id=model.category_id,
            featured=model.featured,
            pricing_category_id=model.pricing_category_id,
            slug=model.slug,
            is_active=model.is_active,

            category=ServiceCategoryResponseDTO.from_model(model.category) if model.category else None,
            pricing_category=PricingCategoryResponseDTO.from_model(model.pricing_category) if model.pricing_category else None,
        )
@dataclass
class ServiceCategoryResponseDTO:
    id: str
    name: str
    description: str
    order: int

    @classmethod
    def from_model(cls, model: ServiceCategory) -> "ServiceCategoryResponseDTO":
        return cls(
            id=model.id,
            name=model.name,
            description=model.description,
            order=model.order,
        )
