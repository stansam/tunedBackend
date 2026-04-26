from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import update
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from tuned.dtos import UpdateUserDTO 
from tuned.models import User
from tuned.repository.user.get import GetUserByID
from tuned.repository.exceptions import NotFound, DatabaseError

class UpdateUser:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, req: UpdateUserDTO, actor_id: Optional[str] = None) -> User:
        try:
            get_user_op = GetUserByID(self.session)
            try:
                user = get_user_op.execute(req.user_id)
            except NotFound as e:
                raise NotFound("User not found") from e
            update_data = req.to_dict()
            allowed_fields = {
                "username",
                "email",
                "first_name",
                "last_name",
                "gender",
                "phone_number",
                "profile_pic",
                "reward_points",
                "language",
                "timezone",
                "password_hash",
                "failed_login_attempts",
                "last_failed_login",
                "last_login_at",
            }
            for key, value in update_data.items():
                if key not in allowed_fields:
                    raise ValueError(f"Field '{key}' is not allowed to be updated")

                if hasattr(user, key):
                    setattr(user, key, value)
                else:
                    raise ValueError(f"Field '{key}' does not exist in user model")
        
            user.updated_at = datetime.now(timezone.utc)
            if actor_id:
                user.updated_by = actor_id
                
            self.session.flush()
            self.session.commit()
            self.session.refresh(user)
            return user

        except SQLAlchemyError as e:
            self.session.rollback()
            raise DatabaseError(f"Database error while updating user: {str(e)}") from e
    
    def increment_failed_login_attempts(self, user_id: str) -> int:
        try:
            stmt = (
                update(User)
                .where(User.id == user_id)
                .values(
                    failed_login_attempts=User.failed_login_attempts + 1
                )
                .returning(User.failed_login_attempts)
            )

            new_count = self.session.execute(stmt).scalar_one()
            self.session.commit()
            return int(new_count)
        except SQLAlchemyError as e:
            self.session.rollback()
            raise DatabaseError(f"Database error while updating user: {str(e)}") from e