from datetime import datetime, timezone
from sqlalchemy import update
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from tuned.dtos import UpdateUserDTO 
from tuned.models import User
from tuned.repository.user.get import GetUserByID
from tuned.repository.exceptions import NotFound, DatabaseError

class UpdateUser:
    def __init__(self, db:Session) -> None:
        self.db = db

    def execute(self, req: UpdateUserDTO) -> User:
        try:
            get_user_op = GetUserByID(self.db)
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
                "language",
                "timezone",
                "password_hash",
                "failed_login_attempts",
                "last_failed_login",
                "last_login_at",
                # "updated_at"
            }
            for key, value in update_data.items():
                if key not in allowed_fields:
                    raise ValueError(f"Field '{key}' is not allowed to be updated")

                if hasattr(user, key):
                    setattr(user, key, value)
                else:
                    raise ValueError(f"Field '{key}' does not exist in user model")
        
            user.updated_at = datetime.now(timezone.utc)
            self.db.flush()
            self.db.commit()
            self.db.refresh(user)
            return user

        except SQLAlchemyError as e:
            self.db.rollback()
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

            new_count = self.db.execute(stmt).scalar_one()
            self.db.commit()
            return new_count
        except SQLAlchemyError as e:
            self.db.rollback()
            raise DatabaseError(f"Database error while updating user: {str(e)}") from e
# from sqlalchemy.orm import Session
# from sqlalchemy.exc import SQLAlchemyError, IntegrityError
# from tuned.dtos import UpdateUserDTO

# from tuned.models import User
# from tuned.repository.exceptions import NotFound, DatabaseError, ConflictError

# class UpdateUser:
#     def __init__(self, db: Session) -> None:
#         self.db = db

#     def execute(self, dto: UpdateUserDTO, actor_id: str | None = None) -> User:
#         try:
#             user: User | None = self.db.query(User).filter_by(id=dto.user_id).first()
#             if not user:
#                 raise NotFound("User not found")

#             update_data = dto.to_update_dict()
#             allowed_fields = {
#                 "username",
#                 "email",
#                 "first_name",
#                 "last_name",
#                 "gender",
#                 "phone_number",
#                 "profile_pic",
#                 "language",
#                 "timezone",
#                 "password_hash"
#             }

#             for field, value in update_data.items():
#                 if field not in allowed_fields:
#                     raise ValueError(f"Field '{field}' is not allowed to be updated")

#                 setattr(user, field, value)

#             self.db.flush()
#             self.db.commit()
#             self.db.refresh(user)

#             return user

#         except (NotFound, ValueError):
#             self.db.rollback()
#             raise

#         except SQLAlchemyError as e:
#             self.db.rollback()
#             raise DatabaseError(f"Failed to update user: {str(e)}") from e