from tuned.models import BlogPost
from tuned.dtos import BlogPostDTO
from tuned.repository.exceptions import NotFound, DatabaseError, AlreadyExists
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

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
        
class GetFeaturedBlogPosts:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self):
        try:
            posts = self.db.query(BlogPost).filter_by(is_featured=True)
            if not posts:
                raise NotFound("posts not found")

            return posts

        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching posts: {str(e)}") from e