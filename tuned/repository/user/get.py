from sqlalchemy import select
from tuned.models import User
from sqlalchemy.orm import Session
from typing import Optional
from sqlalchemy.exc import SQLAlchemyError
from tuned.repository.exceptions import NotFound, DatabaseError

class GetUserByID:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, user_id: str) -> User:
        try:
            stmt = select(User).where(User.id == user_id)
            user = self.session.scalar(stmt)
            if not user:
                raise NotFound("User not found")
            return user
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching user: {str(e)}") from e

class GetUserByEmail:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, email: str) -> User:
        try:
            stmt = select(User).where(User.email == email)
            user = self.session.scalar(stmt)
            if not user:
                raise NotFound("User not found")
            return user
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching user: {str(e)}") from e

class GetUserByUsername:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, username: str) -> User:
        try:
            stmt = select(User).where(User.username == username)
            user = self.session.scalar(stmt)
            if not user:
                raise NotFound("User not found")
            return user
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching user: {str(e)}") from e
        
class GetAdminUser:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self) -> User:
        try:
            stmt = select(User).where(User.is_admin == True)
            user = self.session.scalar(stmt)
            if not user:
                raise NotFound("User not found")
            return user
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching user: {str(e)}") from e

class GetUsers:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self) -> list[User]:
        try:
            stmt = select(User)
            users = self.session.scalars(stmt).all()
            if not users:
                raise NotFound("Users not found")
            return list(users)
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching users: {str(e)}") from e

class GetUserByReferralCode:
    def __init__(self, session: Session) -> None:
        self.session = session
        
    def execute(self, referral_code: str) -> Optional[User]:
        try:
            stmt = select(User).where(User.referral_code == referral_code)
            user = self.session.scalar(stmt)
            return user
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching user by referral code: {str(e)}") from e