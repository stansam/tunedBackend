from tuned.models import BlogCategory, BlogPost, BlogComment, CommentReaction
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.repository.blogs.exceptions import NotFound, DatabaseError

class GetBlogPostBySlug:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, slug: str) -> BlogPost:
        try:
            post = self.db.query(BlogPost).filter_by(slug=slug)
            if not post:
                raise NotFound("post not found")

            return post

        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching post: {str(e)}") from e

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
        
class GetBlogComment:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, id: str) -> BlogComment:
        try:
            comment = self.db.query(BlogComment).filter_by(id=slug)
            if not comment:
                raise NotFound("comment not found")

            return comment

        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching comment: {str(e)}") from e
        
class GetCommentReaction:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, id: str) -> CommentReaction:
        try:
            comment_reaction = self.db.query(CommentReaction).filter_by(id=slug)
            if not comment_reaction:
                raise NotFound("reaction not found")

            return comment_reaction

        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching reaction: {str(e)}") from e