from typing import List
from tuned.models import CommentReaction
from tuned.dtos import CommentReactionDTO, CommentReactionResponseDTO
from tuned.repository.exceptions import NotFound, DatabaseError, AlreadyExists
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

class CreateCommentReaction:
    def __init__(self, session: Session):
        self.session = session
    def execute(self, data: CommentReactionDTO)-> CommentReactionResponseDTO:
        try:
            reaction = CommentReaction(**data.__dict__)

            self.session.add(reaction)
            self.session.commit()
            self.session.refresh(reaction)
            return CommentReactionResponseDTO.from_model(reaction)

        except IntegrityError as e:
            self.session.rollback()
            raise AlreadyExists("reaction already exists")
        except SQLAlchemyError as e:
            self.session.rollback()
            raise DatabaseError("Database error while creating reaction") from e

class GetCommentReaction:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, id: str) -> CommentReactionResponseDTO:
        try:
            comment_reaction = self.session.query(CommentReaction).filter_by(id=id).first()
            if not comment_reaction:
                raise NotFound("reaction not found")

            return CommentReactionResponseDTO.from_model(comment_reaction)

        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching reaction: {str(e)}") from e

class UpdateOrDeleteCommentReaction:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, id: str, data: CommentReactionDTO) -> CommentReactionResponseDTO:
        try:
            comment_reaction = self.session.query(CommentReaction).filter_by(id=id).first()
            if not comment_reaction:
                raise NotFound("reaction not found")
            
            if data.reaction_type:
                comment_reaction.reaction_type = data.reaction_type
            if data.is_deleted:
                comment_reaction.is_deleted = data.is_deleted
                comment_reaction.deleted_at = data.deleted_at
                comment_reaction.deleted_by = data.deleted_by
            if data.updated_at:
                comment_reaction.updated_at = data.updated_at
            if data.updated_by:
                comment_reaction.updated_by = data.updated_by

            self.session.add(comment_reaction)            
            self.session.commit()
            self.session.refresh(comment_reaction)
            return CommentReactionResponseDTO.from_model(comment_reaction)

        except SQLAlchemyError as e:
            self.session.rollback()
            raise DatabaseError(f"Database error while updating reaction: {str(e)}") from e

class  GetCommentReactions:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, comment_id: str) -> List[CommentReactionResponseDTO]:
        try:
            comment_reactions = self.session.query(CommentReaction).filter_by(comment_id=comment_id).all()
            if not comment_reactions:
                return []
            return [CommentReactionResponseDTO.from_model(reaction) for reaction in comment_reactions]
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching reactions: {str(e)}") from e
