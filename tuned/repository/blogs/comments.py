from typing import List
from tuned.models import BlogComment
from tuned.dtos import BlogCommentDTO, BlogCommentResponseDTO # CommentReactionResponseDTO
# from tuned.dtos.blogs import BlogCommentResponseModel
from tuned.repository.exceptions import NotFound, DatabaseError, AlreadyExists
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

class CreateBlogComment:
    def __init__(self, session: Session):
        self.session = session
    def execute(self, data: BlogCommentDTO)-> BlogCommentResponseDTO:
        try:
            data_dict = data.__dict__.copy()
            comment = BlogComment(**data_dict)

            self.session.add(comment)
            self.session.commit()
            self.session.refresh(comment)
            return BlogCommentResponseDTO.from_model(comment)

        except IntegrityError as e:
            self.session.rollback()
            raise AlreadyExists("comment already exists")
        except SQLAlchemyError as e:
            self.session.rollback()
            raise DatabaseError("Database error while creating comment") from e

class GetBlogComment:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, id: str) -> BlogCommentResponseDTO:
        try:
            comment = self.session.query(BlogComment).filter_by(id=id).first()
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
            comment = self.session.query(BlogComment).filter_by(id=id).first()
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
            self.session.commit()
            self.session.refresh(comment)
            return BlogCommentResponseDTO.from_model(comment)

        except SQLAlchemyError as e:
            self.session.rollback()
            raise DatabaseError(f"Database error while updating comment: {str(e)}") from e

class GetBlogComments:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, post_id: str) -> List[BlogCommentResponseDTO]:
        try:
            comments = self.session.query(BlogComment).filter_by(post_id=post_id).all()
            if not comments:
                return []
            # comments = [to_response_model(comment) for comment in comments]

            return [BlogCommentResponseDTO.from_model(comment) for comment in comments]
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching comments: {str(e)}") from e

# def to_response_model(obj: BlogComment) -> BlogCommentResponseModel:
#     return BlogCommentResponseModel(
#         id=str(obj.id),
#         post_id=str(obj.post_id),
#         content=obj.content,
#         name=obj.name,
#         email=obj.email,
#         user_id=str(obj.user_id) if obj.user_id else None,
#         approved=obj.approved,
#         reactions=[
#             CommentReactionResponseDTO.from_model(r)
#             for r in obj.reactions
#         ],
#         total_likes=obj.likes_count,
#         total_dislikes=obj.dislikes_count,
#     )