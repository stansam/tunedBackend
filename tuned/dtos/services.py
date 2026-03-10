from typing import Optional

class ServiceDTO:
    name: str
    description: str
    category_id: str
    featured: bool
    pricing_category_id: str
    slug: Optional[str] = None
    is_active: Optional[bool] = True

class ServiceCategoryDTO:
    name: str
    description: str
    order: int