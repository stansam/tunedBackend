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
            user = self.session.query(User).filter_by(id=user_id).first()
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
            user = self.session.query(User).filter_by(email=email).first()
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
            user = self.session.query(User).filter_by(username=username).first()
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
            user = self.session.query(User).filter_by(is_admin=True).first()
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
            users = self.session.query(User).all()
            if not users:
                raise NotFound("Users not found")
            return users
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching users: {str(e)}") from e

class GetUserByReferralCode:
    def __init__(self, session: Session) -> None:
        self.session = session
        
    def execute(self, referral_code: str) -> Optional[User]:
        try:
            user = self.session.query(User).filter_by(referral_code=referral_code).first()
            return user
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching user by referral code: {str(e)}") from e