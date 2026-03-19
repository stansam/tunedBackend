from dataclasses import dataclass
from typing import Optional
from tuned.models.enums import GenderEnum

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

# @dataclass
# class 