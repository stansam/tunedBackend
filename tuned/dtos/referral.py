from dataclasses import dataclass
from typing import Optional
from datetime import datetime
from tuned.dtos.base import BaseDTO
from tuned.models.enums import ReferralStatus

@dataclass(kw_only=True)
class ReferralCreateDTO:
    referrer_id: str
    referred_id: str
    code: str
    status: Optional[str] = ReferralStatus.PENDING
    commission: Optional[float] = 0.0

@dataclass(kw_only=True)
class ReferralUpdateDTO:
    status: Optional[str] = None
    commission: Optional[float] = None

@dataclass(kw_only=True)
class ReferralResponseDTO(BaseDTO):
    id: str
    referrer_id: str
    referred_id: str
    code: str
    status: str
    commission: float

    @classmethod
    def from_model(cls, model: object) -> 'ReferralResponseDTO':
        return cls(
            id=str(model.id),
            referrer_id=model.referrer_id,
            referred_id=model.referred_id,
            code=model.code,
            status=model.status.value if hasattr(model.status, 'value') else model.status,
            commission=model.commission,
            created_at=model.created_at,
            updated_at=model.updated_at,
            is_deleted=getattr(model, 'is_deleted', False)
        )
