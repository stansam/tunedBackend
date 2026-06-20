from tuned.models import User
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from tuned.repository.exceptions import AlreadyExists, DatabaseError, InvalidCredentials
from tuned.dtos import CreateUserDTO
from datetime import datetime, timezone
class CreateUser:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, user_data: CreateUserDTO) -> User:
        try:
            new_user = User(
                username=user_data.username,
                email=user_data.email,
                first_name=user_data.first_name,
                last_name=user_data.last_name,
                email_verified=user_data.email_verified,
                is_admin=user_data.is_admin,
                gender=user_data.gender,
                phone_number=user_data.phone_number,
                # profile_pic=user_data.profile_pic,
                # braintree_customer_id=user_data.braintree_customer_id,
                # last_login_at=user_data.last_login_at,
                language=user_data.language,
                timezone=user_data.timezone,
                
            )
            
            try:
                new_user.set_password(user_data.password)
            except Exception as e:
                raise InvalidCredentials("Invalid credentials") from e
            
            self.session.add(new_user)
            self.session.flush()

            # new_user.created_at = datetime.now(timezone.utc)
            # new_user.created_by = new_user.id

            return new_user
        except IntegrityError as e:
            raise AlreadyExists("User already exists")
        except SQLAlchemyError as e:
            raise DatabaseError("Database error while creating user") from e