from typing import Optional

class PriceRateDTO:
    pricing_category_id: str
    academic_level_id: str
    deadline_id: str
    price_per_page: float
    is_active: Optional[bool] = True

class PricingCategoryDTO:
    name: str
    desription: str
    display_order: int


