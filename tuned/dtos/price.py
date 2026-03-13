from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Request DTOs
# ---------------------------------------------------------------------------

@dataclass
class PricingCategoryDTO:
    name: str
    description: str = ""
    display_order: int = 0


@dataclass
class PriceRateDTO:
    pricing_category_id: str
    academic_level_id: str
    deadline_id: str
    price_per_page: float
    is_active: Optional[bool] = True


# ---------------------------------------------------------------------------
# Response DTOs
# ---------------------------------------------------------------------------

@dataclass
class PricingCategoryResponseDTO:
    id: str
    name: str
    description: str
    display_order: int

    @classmethod
    def from_model(cls, obj) -> "PricingCategoryResponseDTO":
        return cls(
            id=obj.id,
            name=obj.name,
            description=obj.description or "",
            display_order=obj.display_order,
        )


@dataclass
class PriceRateResponseDTO:
    id: str
    pricing_category_id: str
    academic_level_id: str
    deadline_id: str
    price_per_page: float
    is_active: bool

    @classmethod
    def from_model(cls, obj) -> "PriceRateResponseDTO":
        return cls(
            id=obj.id,
            pricing_category_id=obj.pricing_category_id,
            academic_level_id=obj.academic_level_id,
            deadline_id=obj.deadline_id,
            price_per_page=obj.price_per_page,
            is_active=obj.is_active,
        )


@dataclass
class PriceRateLookupDTO:
    """Used to look up a specific rate by the three FK dimensions."""
    pricing_category_id: str
    academic_level_id: str
    deadline_id: str
