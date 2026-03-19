from tuned.models import CommentReaction
from tuned.dtos import CommentReactionDTO
from tuned.repository.exceptions import NotFound, DatabaseError, AlreadyExists
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

class CreateCommentReaction:
    def __init__(self, db:Session):
        self.db = db
    def execute(self, data: CommentReactionDTO)-> CommentReaction:
        try:
            reaction = CommentReaction(**data)

            self.db.add(reaction)
            self.db.commit()
            return reaction

        except IntegrityError as e:
            self.db.rollback()
            raise AlreadyExists("reaction already exists")
        except SQLAlchemyError as e:
            self.db.rollback()
            raise DatabaseError("Database error while creating reaction") from e

class GetCommentReaction:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, id: str) -> CommentReaction:
        try:
            comment_reaction = self.db.query(CommentReaction).filter_by(id=id)
            if not comment_reaction:
                raise NotFound("reaction not found")

            return comment_reaction

        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching reaction: {str(e)}") from e