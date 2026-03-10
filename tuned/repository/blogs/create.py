from tuned.models import BlogCategory, BlogPost, BlogComment, CommentReaction
from tuned.dtos import BlogPostDTO, BlogCategoryDTO, BlogCommentDTO, CommentReactionDTO
from tuned.repository.blogs.exceptions import AlreadyExists
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

class CreateBlog:
    def __init__(self, db:Session):
        self.db = db
    def execute(self, data: BlogPostDTO)-> BlogPost:
        try:
            post = BlogPost(**data)

            self.db.add(post)
            self.db.commit()
            return post

        except IntegrityError as e:
            self.db.rollback()
            raise AlreadyExists("Post already exists")
        except SQLAlchemyError as e:
            self.db.rollback()
            raise DatabaseError("Database error while creating post") from e
        
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