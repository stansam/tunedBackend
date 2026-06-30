from dataclasses import dataclass
from typing import Optional, Union
from datetime import datetime

@dataclass(kw_only=True)
class BaseDTO:
    is_deleted: Optional[bool] = False
    deleted_at: Optional[Union[datetime, str]] = None
    deleted_by: Optional[str] = None
    updated_at: Optional[Union[datetime, str]] = None
    updated_by: Optional[str] = None
    created_by: Optional[str] = None
    created_at: Optional[Union[datetime, str]] = None

    def __post_init__(self) -> None:
        if isinstance(self.created_at, datetime):
            self.created_at = self.created_at.isoformat()
        if isinstance(self.updated_at, datetime):
            self.updated_at = self.updated_at.isoformat()
        if isinstance(self.deleted_at, datetime):
            self.deleted_at = self.deleted_at.isoformat()

@dataclass(kw_only=True)
class PaginationDTO:
    sort: Optional[str] = "created_at"
    order: Optional[str] = "desc"
    page: Optional[int] = 1
    per_page: Optional[int] = 12

@dataclass(kw_only=True)
class BaseRequestDTO:
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None