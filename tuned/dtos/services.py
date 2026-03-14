from dataclasses import dataclass
from typing import Optional
from tuned.models import Service

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
class ServiceResponseDTO:
    id: str
    name: str
    description: str
    category_id: str
    featured: bool
    pricing_category_id: str
    slug: str
    is_active: bool

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
        )

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
