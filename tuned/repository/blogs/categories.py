from tuned.models import BlogCategory
from tuned.dtos import BlogCategoryDTO
from tuned.repository.exceptions import NotFound, DatabaseError, AlreadyExists
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

class CreateBlogCategory:
    def __init__(self, db:Session):
        self.db = db
    def execute(self, data: BlogCategoryDTO)-> BlogCategory:
        try:
            category = BlogCategory(**data)

            self.db.add(category)
            self.db.commit()
            return category

        except IntegrityError as e:
            self.db.rollback()
            raise AlreadyExists("category already exists")
        except SQLAlchemyError as e:
            self.db.rollback()
            raise DatabaseError("Database error while creating category") from e

class GetBlogCategoryBySlug:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, slug: str) -> BlogCategory:
        try:
            category = self.db.query(BlogCategory).filter_by(slug=slug)
            if not category:
                raise NotFound("post not found")

            return category

        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching post: {str(e)}") from e

