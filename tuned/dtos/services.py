from dataclasses import dataclass
from typing import Optional


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