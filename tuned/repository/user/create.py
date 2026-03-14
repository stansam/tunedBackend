from tuned.models import User
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from tuned.repository.exceptions import AlreadyExists, DatabaseError
from tuned.dtos import CreateUserDTO

class CreateUser:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, user_data: CreateUserDTO) -> User:
        try:
            data = user_data.__dict__.copy()
            password = data.pop('password', None)
            
            new_user = User(**data)
            
            if password:
                new_user.set_password(password)
            
            self.db.add(new_user)
            self.db.commit()
            self.db.refresh(new_user)
            return new_user
        except IntegrityError as e:
            self.db.rollback()
            raise AlreadyExists("User already exists")
        except SQLAlchemyError as e:
            self.db.rollback()
            raise DatabaseError("Database error while creating user") from e