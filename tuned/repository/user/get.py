from tuned.models import User
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from tuned.repository.exceptions import NotFound, DatabaseError

class GetUserByID:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, user_id: str) -> User:
        try:
            user = self.db.query(User).filter_by(id=user_id).first()
            if not user:
                raise NotFound("User not found")
            return user
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching user: {str(e)}") from e

class GetUserByEmail:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, email: str) -> User:
        try:
            user = self.db.query(User).filter_by(email=email).first()
            if not user:
                raise NotFound("User not found")
            return user
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching user: {str(e)}") from e

class GetUserByUsername:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, username: str) -> User:
        try:
            user = self.db.query(User).filter_by(username=username).first()
            if not user:
                raise NotFound("User not found")
            return user
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching user: {str(e)}") from e
        
class GetAdminUser:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self) -> User:
        try:
            user = self.db.query(User).filter_by(is_admin=True).first()
            if not user:
                raise NotFound("User not found")
            return user
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching user: {str(e)}") from e

class GetUsers:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self) -> list[User]:
        try:
            users = self.db.query(User).all()
            if not users:
                raise NotFound("Users not found")
            return users
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching users: {str(e)}") from e