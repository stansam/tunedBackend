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

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime

@dataclass
class UpdateUserDTO:
    user_id: str
    username: Optional[str] = None
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    gender: Optional[str] = None
    phone_number: Optional[str] = None
    profile_pic: Optional[str] = None
    failed_login_attempts: Optional[int] = None
    last_failed_login: Optional[datetime] = None
    last_login_at: Optional[datetime] = None
    language: Optional[str] = None
    timezone: Optional[str] = None
    password_hash: Optional[str] = None
    is_admin: Optional[bool] = field(default=None, repr=False)

    def to_dict(self):
        return {
            k: v for k, v in self.__dict__.items()
            if k != "user_id" and v is not None
        }