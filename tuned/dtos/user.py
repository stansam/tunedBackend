from datetime import timezone, datetime
from dataclasses import dataclass
from typing import Optional
from tuned.models.enums import GenderEnum
# from tuned.dtos.base import BaseDTO

@dataclass
class CreateUserDTO:
    username: str
    email: str
    password: str
    first_name: str
    last_name: str
    email_verified: Optional[bool] = False
    gender: Optional[GenderEnum] = GenderEnum.UNKOWN
    phone_number: Optional[str] = None
    is_admin: Optional[bool] = False
    language: Optional[str] = "en"
    timezone: Optional[str] = "UTC"

@dataclass
class LoginRequestDTO:
    identifier: str
    password: str
    remember_me: Optional[bool] = False

@dataclass
class UserResponseDTO:
    id: str
    email: str
    name: str
    avatar_url: str
    # role: str
    session_created_at: Optional[str] = None

    @classmethod
    def from_model(cls, obj) -> "UserResponseDTO":
        return cls(
            id=str(obj.id),
            email=obj.email,
            name=f"{obj.first_name} {obj.last_name}",
            avatar_url=obj.profile_pic,
            # role=obj.role,
            session_created_at=datetime.now(timezone.utc).isoformat(),
        )