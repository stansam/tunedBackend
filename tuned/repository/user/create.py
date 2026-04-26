from tuned.models import User
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from tuned.repository.exceptions import AlreadyExists, DatabaseError
from tuned.dtos import CreateUserDTO
from datetime import datetime, timezone
class CreateUser:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, user_data: CreateUserDTO) -> User:
        try:
            data = user_data.__dict__.copy()
            password = data.pop('password', None)
            
            new_user = User(**data)  # type: ignore[no-untyped-call]
            
            if password:
                new_user.set_password(password)  # type: ignore[no-untyped-call]
            
            self.session.add(new_user)
            self.session.flush()

            new_user.created_at = datetime.now(timezone.utc)
            new_user.created_by = new_user.id

            self.session.commit()
            self.session.refresh(new_user)

            return new_user
        except IntegrityError as e:
            self.session.rollback()
            raise AlreadyExists("User already exists")
        except SQLAlchemyError as e:
            self.session.rollback()
            raise DatabaseError("Database error while creating user") from e