from datetime import datetime, timezone
from tuned.models import BlogCategory
from tuned.dtos import BlogCategoryDTO, BlogCategoryResponseDTO
from tuned.repository.exceptions import NotFound, DatabaseError, AlreadyExists
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

class CreateBlogCategory:
    def __init__(self, db:Session):
        self.db = db
    def execute(self, data: BlogCategoryDTO)-> BlogCategoryResponseDTO:
        try:
            data_dict = data.__dict__.copy()
            category = BlogCategory(**data_dict)

            self.db.add(category)
            self.db.commit()
            return BlogCategoryResponseDTO.from_model(category)

        except IntegrityError as e:
            self.db.rollback()
            raise AlreadyExists("category already exists")
        except SQLAlchemyError as e:
            self.db.rollback()
            raise DatabaseError(f"Database error while creating category:\n {str(e)}")

class GetBlogCategoryBySlug:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, slug: str) -> BlogCategoryResponseDTO:
        try:
            category = self.db.query(BlogCategory).filter_by(slug=slug)
            if not category:
                raise NotFound("post not found")

            return BlogCategoryResponseDTO.from_model(category)

        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching post: {str(e)}") from e
    
class ListBlogCategories:
    def __init__(self, db: Session) -> None:
        self.db = db
    
    def execute(self) -> list[BlogCategoryResponseDTO]:
        try:
            categories = self.db.query(BlogCategory).all()
            return [BlogCategoryResponseDTO.from_model(category) for category in categories]
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching categories: {str(e)}") from e

class UpdateOrDeleteBlogCategory:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, id: str, data: BlogCategoryDTO) -> BlogCategoryResponseDTO:
        try:
            comment_reaction = self.db.query(BlogCategory).filter_by(id=id).first()
            if not comment_reaction:
                raise NotFound("reaction not found")
            
            if data.is_deleted:
                comment_reaction.is_deleted = data.is_deleted
                comment_reaction.deleted_at = datetime.now(timezone.utc)
                comment_reaction.deleted_by = data.deleted_by
            else:
                if data.name:
                    comment_reaction.name = data.name
                if data.description:
                    comment_reaction.description = data.description
                if data.updated_by:
                    comment_reaction.updated_by = data.updated_by
                    comment_reaction.updated_at = datetime.now(timezone.utc)

            self.db.add(comment_reaction)            
            self.db.commit()
            self.db.refresh(comment_reaction)
            return BlogCategoryResponseDTO.from_model(comment_reaction)

        except SQLAlchemyError as e:
            self.db.rollback()
            raise DatabaseError(f"Database error while updating reaction: {str(e)}") from e
