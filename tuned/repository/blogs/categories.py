from datetime import datetime, timezone
from tuned.models import BlogCategory
from tuned.dtos import BlogCategoryDTO, BlogCategoryResponseDTO
from tuned.repository.exceptions import NotFound, DatabaseError, AlreadyExists
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

class CreateBlogCategory:
    def __init__(self, session: Session):
        self.session = session

    def execute(self, data: BlogCategoryDTO) -> BlogCategoryResponseDTO:
        try:
            data_dict = data.__dict__.copy()
            category = BlogCategory(**data_dict)

            self.session.add(category)
            self.session.flush()
            return BlogCategoryResponseDTO.from_model(category)

        except IntegrityError as e:
            raise AlreadyExists("category already exists")
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while creating category:\n {str(e)}")

class GetBlogCategoryBySlug:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, slug: str) -> BlogCategoryResponseDTO:
        try:
            stmt = select(BlogCategory).where(BlogCategory.slug == slug)
            category = self.session.scalar(stmt)
            if not category:
                raise NotFound("post not found")

            return BlogCategoryResponseDTO.from_model(category)

        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching post: {str(e)}") from e
    
class ListBlogCategories:
    def __init__(self, session: Session) -> None:
        self.session = session
    
    def execute(self) -> list[BlogCategoryResponseDTO]:
        try:
            stmt = select(BlogCategory)
            categories = self.session.scalars(stmt).all()
            return [BlogCategoryResponseDTO.from_model(category) for category in categories]
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching categories: {str(e)}") from e

class UpdateOrDeleteBlogCategory:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, id: str, data: BlogCategoryDTO) -> BlogCategoryResponseDTO:
        try:
            stmt = select(BlogCategory).where(BlogCategory.id == id)
            category = self.session.scalar(stmt)
            if not category:
                raise NotFound("category not found")
            
            if data.is_deleted:
                category.is_deleted = data.is_deleted
                category.deleted_at = datetime.now(timezone.utc)
                category.deleted_by = data.deleted_by
            else:
                if data.name:
                    category.name = data.name
                if data.description:
                    category.description = data.description
                if data.updated_by:
                    category.updated_by = data.updated_by
                    category.updated_at = datetime.now(timezone.utc)

            self.session.add(category)            
            self.session.flush()
            return BlogCategoryResponseDTO.from_model(category)

        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while updating category: {str(e)}") from e
