from datetime import timezone, datetime
from dataclasses import dataclass, field
from typing import Optional
from tuned.models.enums import GenderEnum
from tuned.dtos.base import BaseRequestDTO

@dataclass
class CreateUserDTO:
    username: str
    email: str
    password: str
    first_name: str
    last_name: str
    email_verified: bool = False
    gender: GenderEnum = GenderEnum.UNKNOWN
    is_admin: bool = False
    language: str = "en"
    timezone: str = "UTC"
    phone_number: Optional[str] = None

@dataclass
class LoginRequestDTO(BaseRequestDTO):
    identifier: str
    password: str
    remember_me: Optional[bool] = False

@dataclass
class UserResponseDTO:
    id: str
    name: str
    email: str
    avatar_url: str
    # role: str
    session_created_at: Optional[str] = None

    @classmethod
    def from_model(cls, obj) -> "UserResponseDTO":
        return cls(
            id=str(obj.id),
            name=" ".join(filter(None, [obj.first_name, obj.last_name])),
            email=obj.email,
            avatar_url=obj.get_profile_pic_url(),
            # role=obj.role,
            session_created_at=datetime.now(timezone.utc).isoformat(),
        )

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


@dataclass
class EmailVerificationResendDTO(BaseRequestDTO):
    email: str


@dataclass
class EmailVerifyConfirmDTO(BaseRequestDTO):
    uid: str
    token: str