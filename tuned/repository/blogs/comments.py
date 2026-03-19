from tuned.models import BlogComment
from tuned.dtos import BlogCommentDTO
from tuned.repository.exceptions import NotFound, DatabaseError, AlreadyExists
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

class CreateBlogComment:
    def __init__(self, db:Session):
        self.db = db
    def execute(self, data: BlogCommentDTO)-> BlogComment:
        try:
            comment = BlogComment(**data)

            self.db.add(comment)
            self.db.commit()
            return comment

        except IntegrityError as e:
            self.db.rollback()
            raise AlreadyExists("comment already exists")
        except SQLAlchemyError as e:
            self.db.rollback()
            raise DatabaseError("Database error while creating comment") from e

class GetBlogComment:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, id: str) -> BlogComment:
        try:
            comment = self.db.query(BlogComment).filter_by(id=id)
            if not comment:
                raise NotFound("comment not found")

            return comment

        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching comment: {str(e)}") from e

