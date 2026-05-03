from typing import List
from tuned.models import BlogComment
from tuned.dtos import BlogCommentDTO, BlogCommentResponseDTO
from tuned.repository.exceptions import NotFound, DatabaseError, AlreadyExists
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

class CreateBlogComment:
    def __init__(self, session: Session):
        self.session = session

    def execute(self, data: BlogCommentDTO) -> BlogCommentResponseDTO:
        try:
            data_dict = data.__dict__.copy()
            comment = BlogComment(**data_dict)

            self.session.add(comment)
            self.session.flush()
            return BlogCommentResponseDTO.from_model(comment)

        except IntegrityError as e:
            raise AlreadyExists("comment already exists")
        except SQLAlchemyError as e:
            raise DatabaseError("Database error while creating comment") from e

class GetBlogComment:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, id: str) -> BlogCommentResponseDTO:
        try:
            stmt = select(BlogComment).where(BlogComment.id == id)
            comment = self.session.scalar(stmt)
            if not comment:
                raise NotFound("comment not found")

            return BlogCommentResponseDTO.from_model(comment)

        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching comment: {str(e)}") from e

class UpdateOrDeleteBlogComment:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, id: str, data: BlogCommentDTO) -> BlogCommentResponseDTO:
        try:
            stmt = select(BlogComment).where(BlogComment.id == id)
            comment = self.session.scalar(stmt)
            if not comment:
                raise NotFound("comment not found")
            
            if data.content:
                comment.content = data.content
            if data.approved:
                comment.approved = data.approved
            if data.is_deleted:
                comment.is_deleted = data.is_deleted
                comment.deleted_at = data.deleted_at
                comment.deleted_by = data.deleted_by
            if data.updated_at:
                comment.updated_at = data.updated_at
            if data.updated_by:
                comment.updated_by = data.updated_by

            self.session.add(comment)            
            self.session.flush()
            return BlogCommentResponseDTO.from_model(comment)

        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while updating comment: {str(e)}") from e

class GetBlogComments:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, post_id: str) -> List[BlogCommentResponseDTO]:
        try:
            stmt = select(BlogComment).where(BlogComment.post_id == post_id)
            comments = self.session.scalars(stmt).all()
            return [BlogCommentResponseDTO.from_model(comment) for comment in comments]
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching comments: {str(e)}") from e