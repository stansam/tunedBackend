from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass(kw_only=True)
class BaseDTO:
    is_deleted: Optional[bool] = False
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[str] = None
    updated_at: Optional[datetime] = None
    updated_by: Optional[str] = None
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None


@dataclass(kw_only=True)
class PaginationDTO:
    sort: Optional[str] = "created_at"
    order: Optional[str] = "desc"
    page: Optional[int] = 1
    per_page: Optional[int] = 12
    
    @classmethod
    def from_model(cls, model: Any) -> 'PaginationDTO':
        return cls(
            sort=model.sort,
            order=model.order,
            page=model.page,
            per_page=model.per_page,
        )

@dataclass(kw_only=True)
class BaseRequestDTO:
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None